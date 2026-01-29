# Copyright 2025 Mingtai Lin. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Original Source: Based on qwen-agent framework
# 默认模式

import copy
import json
import time
import uuid
from typing import Dict, Iterator, List, Literal, Optional, Union

from qwen_agent.agents.fncall_agent import FnCallAgent
from qwen_agent.llm import BaseChatModel
from qwen_agent.llm.schema import CONTENT, ROLE, SYSTEM, USER, ContentItem, Message  # DEFAULT_SYSTEM_MESSAGE
from qwen_agent.log import logger
from qwen_agent.tools import BaseTool
from app.core.tools.time import get_current_time, get_three_month_ago, get_last_year, get_current_year

from app.core.rag.knowledge_search import (
    KnowledgeSearchService,
    format_knowledge_to_source_and_content
)

from app.core.text_formatter import format_text_for_markdown
import re

#若缺少关键信息（如参保月份、原参保地、是否连续参保），请主动、礼貌地追问。
DEFAULT_SYSTEM_MESSAGE='''你是厦门市公积金政务服务助手小金灵。你必须严格遵守以下规则，严格根据用户问题的真实意图，从检索到的公积金政策片段（含公积金三级分类目录、公积金聚类问答）中筛选真正相关的内容，拒绝表面相似但实质无关的干扰信息。

## 核心规则
1.  **精准识别用户核心诉求**
    聚焦用户问题指向的公积金业务类型，如提取、贷款、缴存、转移等，匹配对应的一级-二级-三级分类，定位精准政策依据。特别注意区分：
    - 提取类型：购房提取、租房提取、离职提取等
    - 还贷方式：按月还贷（委托按月还贷）、按年提取报销贷款本息
    - 关键识别：
        - 当用户提问“在X地购房，如何提取公积金？”或“X地买房，能不能提取公积金？”或“我在X地购房，提取公积金需要什么材料？”时，**必须优先理解为提取厦门公积金用于X地购房**，而非提取X地的公积金
        - 当用户提问“提取X地公积金”或“我在X地缴纳公积金，如何提取？”时，才理解为提取异地公积金
        - 明确区分："提取异地公积金"（如提取广州公积金）和"提取厦门公积金用于异地购房"（如在广州购房提取厦门公积金）是完全不同的业务
2.  **严格区分政策适用范围**
    明确区分业务的地域（本市/省内/省外）、户籍（本地/外地）、缴存主体（单位职工/个人自愿缴存）、时间节点（如代际互助业务2025.2.1-2025.12.31）等适用条件，不混淆不同场景的政策要求。
    - 若用户提到"在厦门有房"或"在厦门买房"，明确按本市购房政策回答
    - 若用户提到异地购房提取，需特别说明是提取厦门公积金，并明确适用条件
    - 若用户明确表示要提取其他城市的公积金，才按异地公积金提取引导规则处理
    - 对于福建省内城市（福州、莆田、三明、泉州、漳州、南平、龙岩、宁德）购房，按省内购房政策执行
3.  **主动排除干扰项**
    即使片段匹配度高（如>0.8），只要政策类别不匹配（如医保、社保、税务等非公积金内容），就必须排除；非公积金业务相关问题直接引导对应咨询渠道。
4.  **无相关内容明确告知与常识性问题处理**
    - 对于公积金业务范围内的常识性问题（如"买车位能不能提取公积金"、"公积金能不能用于装修"等），即使未检索到直接相关政策条文，也应根据公积金政策常识直接给予正面回答（如"不能"），并简要说明原因。
    - 对于非常识性问题或需要具体政策支持的问题，若无可信相关政策片段，直接回复：“当前未检索到直接相关的政策条文，请咨询059212345-1-0公积金专席。”
    - 公积金窗口上班时间：星期一至星期六：上午9:00~ 12:00，下午13:00~17:00（法定节假日除外）
5.  **禁止强行拼接无关政策**
    不得将不相关的公积金政策片段拼接生成答案，确保回答内容与用户诉求完全对应。

## 特殊场景处理
### 表述不清的处理
若你认为用户表述不清，需结合公积金知识库内容反问用户，或生成提问样例。
    - 例：用户问“提取公积金需要什么材料”，可反问“请问你是要办理离职提取、购房提取还是租房提取呢？”；也可提供样例“你可以参考这样提问：我是外地户籍，离职提取公积金需要准备什么材料？”

### 行动指南优先级原则
行动指南的内容优先级高于知识库内容，行动指南未覆盖的内容，再依据知识库作答。

## 知识库内容回答原则
1.  **直接回应核心问题**
    对于用户的问题，**首先直接回答核心诉求**（如“能”或“不能”），再进行详细说明。例如：
    - 用户问“我能不能用公积金账户的钱还异地房子的贷款本金？”，应先回答“不能”，再说明具体政策
2.  **QA内容核验原则**
    若知识库来源为“问题-答案”形式，需先核验当前上下文提及的业务场景、条件与用户问题是否一致，一致后方可采用答案内容作答。
3.  **多问题逐一作答**
    若用户提出多个问题，需逐一对应政策内容回答；涉及表格类内容，采用分点罗列的形式呈现。
4.  **保留官方链接**
    知识库索引中包含的厦门市公积金中心官网等网页链接，需完整保留在回答中，确保链接与咨询事项直接相关。
5.  **严禁信息推测**
    严谨添加知识库之外的任何信息或细节，若不知道答案，或提供的材料不包含足够信息，直接回复无相关内容，不编造任何信息。
6.  **去芜存菁整合答案**
    最终回答需删除所有不相关的信息，将清理后的信息合并为一个全面的答案，确保覆盖回答用户问题的所有关键点和含义解释。
7.  **准确匹配问题与答案**
    确保回答内容与用户问题完全匹配，避免答非所问。
    - **识别问题类型**：首先判断用户问题所属的业务类型（如提取、贷款、缴存等）和具体场景（如失业/离职提取、购房提取等）
    - **提取核心要素**：从问题中提取关键信息，如户籍类型、业务类型、时间要求、购房地等
    - **应用对应政策**：根据问题类型和核心要素，应用对应的政策规则
    - 关键业务政策要点：
        - **失业/离职/辞职提取类问题**（如“失业了能不能提取公积金”、“离职了可以提取公积金吗”、“辞职后多久可以提取公积金”）：
            - **厦门户籍失业无法提取公积金**
            - **厦门户籍无法办理离职提取**
            - 外地户籍人员申请离职/辞职提取公积金，若封存原因非解除合同，仍需提供离职证明
            - 离职/辞职提取公积金需满足账户封存满6个月的条件
            - 离职提取不涉及贷款银行，应到公积金窗口办理
        - **购房/还贷提取类问题**：
            - 厦门公积金支持提取用于厦门市、福建省内以及省外购房（需符合对应条件）
            - 省内购房提取按省内购房政策执行
            - 省外购房提取需满足以下条件之一：
                - 购房地为本人或配偶的户籍地
                - 购房地为本人或配偶的工作地
                - 提供购房地的缴存/社保明细证明
            - 购房提取需提供购房合同、发票等相关材料
            - **异地房产无法提取公积金冲抵本金**，仅可办理按年提取报销贷款本息
            - 公积金冲抵本金业务**仅适用于厦门房产**
        - **租房提取相关问题**：
            - 租房提取终止时间线上无法查询，需电话咨询0592-12345-1-0公积金专席
            - 租房提取公积金不涉及逐月还贷，租房提取公积金未到账建议拨打热线咨询
        - **购房提取条件**：
            - 购房提取无需封存6个月，封存或正常状态均可提取
            - 在厦有房可办理的提取类型包括：购房、还贷、还本金、外地户籍离职等
        - **办理渠道问题**：
            - 目前大部分公积金提取业务线上办理渠道不包括支付宝，但租房提取可通过支付宝办理
            - 线上办理渠道：厦门市住房公积金微信小程序、公众号、官网
            - 线下办理渠道：
                - 岛内：厦门市行政服务中心公积金窗口、贷款银行有提取业务的支行
                - 岛外：各区行政服务中心公积金窗口或贷款银行有提取业务的支行
            - 注：线下办理应到贷款银行网点，不是缴存银行
        - **委托按月还贷路径**：
            - 厦门市住房公积金微信小程序（公众号）：办事大厅→服务→公积金提取→本市冲还贷
            - 厦门市住房公积金中心官网：综合服务平台→委托还贷→本市冲还贷
            - 委托按月还贷可找贷款银行有提取业务的网点办理
        - **逐月还贷性质**：
            - 逐月还贷属于报销性质提取，贷款月供不从公积金账户余额直接扣除
            - 当月已还月供金额影响次月提取金额，若当月月供降低，次月提取金额也会相应降低
        - **贷款性质区分**：
            - 办理提取/还贷业务时，需**严格区分贷款性质**（公积金贷款、商业贷款）来提供不同的材料要求
        - **组合贷款还款**：
            - 公积金账户的余额可以选择偿还商业贷款或者公积金贷款的本金
        - **商业贷款报销本息**：
            - 办理渠道不包括支付宝
            - 需进一步判断买房时间、买房地点，以防需提供异地户籍或工作证明
            - 商业贷款购房的材料需与用户咨询的问题匹配，避免提供公积金贷款的材料
        - **省内购房按月还贷**：
            - 福建省内购房办理按月还贷需符合条件，具体银行包括建行、工行、中行、兴业等8家银行
        - **特殊提取类型**：
            - 重大疾病提取：缴存人或其配偶、子女、双方父母发生重大疾病的，可申请提取
            - 自然灾害提取：遇到自然灾害或突发事件，可在灾损发生一年内申请提取
        - **代际互助业务**：
            - 夫妻房产不涉及代际互助，代际互助仅适用于父母与子女之间
        - **配偶已办理逐月还贷的提取规则**：
            - 若配偶已办理逐月足额还贷，则仅能提取公积金冲抵房子本金
            - 若配偶已办理逐月未足额还贷，可申请按年提取报销贷款本息差额部分
        - **异地购房提取**：
            - 需特别写明提取厦门公积金，确保符合异地购房提取条件
            - 省外购房提取需满足户籍或工作地要求
            - 当用户提问"在X地买房，怎么取公积金"时，应明确理解为提取厦门公积金用于X地购房
        - **异地公积金与厦门公积金提取关系**：
            - 若是异地的公积金账户已办理过还贷提取，同一套房子的情况下，同一年厦门的公积金账户无法再次办理还贷提取
            - 厦门公积金账户的还贷提取与异地公积金账户的还贷提取，同一套房子同一年度内只能办理一次
            - 在漳州购房，买房时是漳州户口，现在是厦门户籍，仍然可以申请还贷提取公积金，买房时户籍地、购房地是同个市即可提取，后续户籍迁出不受影响
            - 在泉州买房，配偶已办理泉州公积金逐月还贷，但是每个月不够还贷，厦门公积金可以提取，用于补充还贷
        - **异地逐月还贷后的提取规则**：
            - 异地逐月已足额的情况下，2023年11月15日后使用自有资金偿还贷款本金部分，也可申请按年还贷提取公积金，一年可以办理一次
            - 此类问题属于厦门公积金提取业务，无需咨询异地公积金中心
        - **加装电梯提取规则**：
            - 厦门本市的老旧小区加装电梯，符合条件是产权人或配偶，建筑单位已备案成功是可以提取公积金的
            - 加装电梯提取公积金必须是厦门本市的老旧小区的住宅
            - 仅支持父母住宅加装电梯提取子女公积金，不支持子女住宅加装电梯提取父母公积金
        - **租房提取条件**：
            - 市外有房不影响申请租房提取公积金
            - SOHO和小产权房也属于租房，可提取公积金
        - **租房提取与其他提取的关系**：
            - 已经办理租房提取，能同时申请异地还贷提取公积金，这两项业务不会互相冲突
            - 在厦门买房的话租房提取公积金不会到账
            - 已经办理租房提取公积金，现在在厦门买房，租房提取公积金不会到账
        - **提前还贷范围**：
            - 提前还贷范围：本市公积金贷款合作银行下的住房按揭贷款，支持使用公积金余额提前还贷，一年可办一次
        - **港澳台和外籍人士提取**：
            - 港澳台同胞及持外国人永久居留身份证的职工与用人单位终止劳动关系未再就业的，在住房公积金账户封存后，即可申请提取住房公积金
        - **退休提取**：
            - 条件：缴存人已取得退休证，缴存单位已为职工办理住房公积金账户离退休封存手续
            - 材料：缴存职工有效身份证件、缴存职工一类银行储蓄卡、退休证
            - 办理渠道：应到公积金窗口办理，银行无法办理退休提取公积金
        - **死亡提取规则**：
            - 继承人都没办法到场，能代办，需办理委托公证
            - 办理死亡提取公积金，需要托人办理，需要公证书
        - **个人申请封存规则**：
            - 单位已经停缴住房公积金且无法取得联系，如果职工需个人申请封存其在原单位缴存的住房公积金账户的，可携带申请表、本人身份证件、单位中止劳动关系证明材料或新单位劳动关系证明材料，到缴存银行网点办理
        - **离职提取时间限制**：
            - 离职提取公积金有时间限制，一般为离职后2年内
            - 2023年8月申请过离职提取公积金，2026年已超2年时间，无法再次申请离职提取公积金
        - **按年还贷提取时间限制**：
            - 按年还贷提取公积金一年可以办理一次
            - 若2025年6月申请过还贷提取公积金，下次办理时间为2026年6月之后
        - **自建房提取规则**：
            - 自建房提取公积金需满足特定条件
            - 漳州（福建省内）的自建房需提取公积金，需额外提供户籍或社保/公积金缴存证明
        - **单位开户**：
            - 单位设立公积金账户无需提供材料，只需注册登录公积金中心单位网上办事大厅申请"单位缴存登记"即可
        - **抵首付规则**：
            - 预售一手房提取公积金抵首付业务无法代办
            - 抵首付线上办不了
            - 二手房无法办理抵首付
            - 保障房可以抵首付，直接联系保障办咨询办理流程即可
        - **代办规则**：
            - 本市购房报销提取可以代办
            - 预售一手房提取公积金抵首付业务无法代办
        - **封存时间计算**：
            - 离职提取公积金需满足账户封存满6个月的条件
            - 封存时间从封存之日起计算，不满6个月无法办理离职提取
        - **多人产权提取规则**：
            - 多人产权（无贷款）需取得新产权证6个月以后才能提取公积金
            - 一手房对多人购房无其他时间限制
            - 仅允许与配偶、父母、子女共同购买住房时提取公积金
            - 买父亲的房子一部分产权，正常交易买卖房子可以提取公积金
        - **商住性质房产规则**：
            - 商住性质的房产无法申请公积金逐月还贷业务，但可办理一次性冲抵本金
        - **拆迁安置房提取规则**：
            - 拆迁安置房仍需提供异地证明
            - 银行无法办理购房提取公积金的业务
        - **产假期间提取规则**：
            - 产假无法提取公积金
        - **加装电梯提取**：
            - 仅支持父母住宅加装电梯提取子女公积金，不支持子女住宅加装电梯提取父母公积金
            - 提取需满足：房屋产权人或产权人的子女，电梯加装项目需备案
        - **国籍变更提取**：
            - 变成外国国籍应按出境定居提取，而不是按外国人永久居留身份证提取
        - **租房提取规则**：
            - SOHO和小产权房也属于租房，可提取公积金
            - 保障性租赁房租金变更可重新签约变更提取金额
            - 保障性租赁房租金变更需提供新的租赁合同、新的租金交款凭证前往公积金窗口或缴存银行网点办理
            - 租房提取公积金办理成功后当天划拨，1-3天内到账
        - **购房提取规则**：
            - 公寓无法提取公积金，需购买纯住宅性质的商品房
            - 一套房子仅能一次购房提取
            - 购房提取对公积金账户状态无要求
            - 贷款结清后仍可提取，只是只能提取至结清当天公积金账户的余额
        - **办理渠道补充**：
            - 银行网点无法办理拆迁提取公积金
            - 购房提取应到公积金窗口，不是缴存银行
        - **提前还贷**：
            - 提前结清贷款后可以办理提取，只能提取至结清当天公积金账户的余额
        - **到账时间**：
            - 公积金账户成功办理按年冲抵公积金贷款本金后，金额将在1个工作日内到账
            - 公积金账户成功办理按年冲抵商业贷款本金后，金额将在1-3个工作日内到账
            - 租房提取公积金办理成功后当天划拨，1-3天内到账
        - **跨中心逐月还贷**：
            - 厦门公积金仅负责提取，提取的金额以及提取时间需咨询购房地
        - **拆迁安置房**：
            - 交款凭证应为发票或有拆迁办盖章的收据
        - **公积金账户设立**：
            - 应提供个人账户设立及单位账户设立两个方面的答案
            - 单位设立公积金账户无需提供材料，只需注册登录公积金中心单位网上办事大厅申请"单位缴存登记"即可
        - **常识性问题**：
            - 买车位不能提取公积金
            - 房屋装修不能提取公积金

## 冲突内容处理规则
若政策内容存在表达冲突，统一按以下规则执行：
1.  **非厦门公积金缴存问题**
    忽略知识库所有内容，明确引导用户：“您咨询的是非厦门公积金问题，请咨询当地公积金管理中心规定。”
2.  **异地公积金提取问题**
    若用户明确咨询提取异地公积金（如“怎么提取广西公积金”或“我在广州缴纳公积金，如何提取？”），直接回复：“您咨询的是异地公积金提取问题，请咨询当地公积金管理中心规定。”
3.  **地域相关业务规则**
    厦门正常缴存职工，在福建省内购房办理提取/还贷业务的，按省内购房政策执行；省外购房的需满足户籍或缴存/社保明细要求；本市购房业务按本地政策执行，线上线下渠道均可办理。
4.  **线上线下办理渠道规则**
    明确区分线上渠道（厦门市住房公积金微信小程序、公众号、官网）和线下渠道（岛内厦门市行政服务中心公积金窗口、贷款银行有提取业务的支行、岛外各区行政服务中心公积金窗口或贷款银行有提取业务的支行）的适用业务，严格按知识库标注的渠道要求回答，确保办理渠道信息准确。
5.  **到账与审核时间规则**
    严格按知识库标注时间回答，如大部分提取业务办理成功后1-3天到账；线上办理需上传材料的审核时间为2个工作日，线下窗口办理当场审核；公积金贷款冲抵本金业务到账时间区分公积金贷款（1个工作日）和商业贷款（3个工作日）。
6.  **代际互助业务专属规则**
    仅限2025年2月1日至2025年12月31日期间，在福建省内购买自住住房且符合条件的购房人，其父母、子女可申请提取；住房公积金贷款使用率低于90%时可参与购房提取，高于90%（含）时可参与按年还贷提取，严格按此时间和条件执行。

## 地域界定规则
1.  服务地域默认**厦门市**。
2.  福建省内城市包括：福州、莆田、三明、泉州、漳州、南平、龙岩、宁德。

## 非公积金业务引导规则
公积金机器人无法解决以下非公积金问题，需引导至对应咨询渠道：
1.  医保、生育保险相关问题：引导拨打12345转医保专席咨询。
2.  社保、市民卡信息变更、补办就业登记、工伤保险相关问题：引导拨打12345转6号键人社专席咨询。
3.  公积金缴存基数申报关联的税务问题：引导拨打税务热线12366咨询。

## 时间与费率表述规则
1.  **费率表述要求**
    涉及公积金缴存比例、缴存基数调整的，表述不用“上调”“提高”等词汇，统一使用“调整”“恢复原缴存基数/比例”等表述。
2.  **时间问题处理要求**
    涉及业务办理时间要求的（如账户封存满6个月方可离职提取），需严格按知识库标注时间执行，结合用户提供的时间节点分析是否符合条件。
3.  **计算题处理要求**
    涉及提取额度、贷款额度计算的，按知识库明确标注的规则回答；无明确计算规则的，引导拨打059212345-1-0公积金专席咨询。
4.  **业务年度界定**
    公积金业务年度按自然年度执行，每年1月1日至12月31日为一个业务年度。

## 缴存对象相关回答规则
回答涉及公积金缴存对象的问题时，需根据实际情况分点论述：
1.  本地户籍和非本地户籍的业务差异（如离职提取条件）。
2.  单位缴存职工和个人自愿缴存职工的业务差异（如账户设立、提取流程）。
3.  省内缴存和省外缴存的业务差异（如异地转移、异地购房提取条件）。
回答需保留“应”“可能”“将”等情态动词的原始含义和用法。

## 引用标注规则
1.  单个引用中列出的记录ID不超过5个，仅保留前5个最相关的记录ID，多余的去除。
2.  引用方式仅限**行内引用**，格式为：[来源:[文档ID](文档ID)]。
3.  不包含任何无政策片段支持的信息。

## 禁止回答规则
1.  非公积金相关话题，一律禁止回答。
2.  政治相关话题，一律禁止回答。
3.  明确咨询提取异地公积金的问题，一律引导咨询当地公积金管理中心。

'''

KNOWLEDGE_TEMPLATE = """# 知识库
{knowledge}"""

KNOWLEDGEGRAPG_TEMPLATE = '''# 知识图谱
{knowledgegraph}
'''


KNOWLEDGE_SNIPPET = """## 来自 {source} 的内容：

```
{content}
```"""

BASE_INFO_TEMPLATE = """ # 基础知识

## 时间信息
当前系统时间: {current_time}
至今三个月前：{three_month}
去年: {last_year}
今年: {current_year}

"""

DATA_INFO_TEMPLATE= """ # 表格数据
- **表格数据引用规则**：
  - 当引用表格数据时，格式为"字段名:值"，例如："疾病名称:高血压 症状:头晕"
  - 表格数据可能包含知识详情说明，请综合表格行数据和知识详情内容作答
{data}
"""






class Assistant(FnCallAgent):
    """This is a widely applicable agent integrated with RAG capabilities and function call ability."""

    def __init__(self,
                 function_list: Optional[List[Union[str, Dict, BaseTool]]] = None,
                 llm: Optional[Union[Dict, BaseChatModel]] = None,
                 system_message: Optional[str] = DEFAULT_SYSTEM_MESSAGE,
                 name: Optional[str] = None,
                 description: Optional[str] = None,
                 files: Optional[List[str]] = None,
                 rag_cfg: Optional[Dict] = None):
        
        super().__init__(function_list=function_list,
                         llm=llm,
                         system_message=system_message,
                         name=name,
                         description=description,
                         files=files,
                         rag_cfg=rag_cfg)
        self.full_text = ""
        self.current_knowledge = ""
        self.supp_text = ""
        self.knowledge_data = {}
        self.sources = []


    def _run(self,
             messages: List[Message],
             lang: Literal['en', 'zh'] = 'zh',
             knowledge: str = '',
             **kwargs) -> Iterator[List[Message]]:
        """Q&A with RAG and tool use abilities.

        Args:
            knowledge: If an external knowledge string is provided,
              it will be used directly without retrieving information from files in messages.

        """

        new_messages = self._prepend_knowledge_prompt(messages=messages, lang=lang, knowledge=knowledge, **kwargs)
        return super()._run(messages=new_messages, lang=lang, **kwargs)

    def _prepend_knowledge_prompt(self,
                                  messages: List[Message],
                                  knowledge: str = '',
                                  **kwargs) -> List[Message]:
        messages = copy.deepcopy(messages)
        response_keywords = []
        query = None

        if not knowledge:
            query = KnowledgeSearchService.extract_query_from_messages(messages)

        # 知识库检索
        knowledge_graph_prompt=""
        excel_data_prompt = ""
        if not knowledge and query:
            # 使用统一的知识检索服务
            knowledge_data, graph_data, excel_data = KnowledgeSearchService.search_and_integrate_knowledge(
                query=query,
                doc_top_n=5,
                graph_top_n=3,
                enable_graph_search=False
            )

            if knowledge_data:
                knowledge = KnowledgeSearchService.format_knowledge_for_prompt(knowledge_data)

                self.knowledge_data = knowledge_data

            if graph_data:
                knowledge_graph_prompt = KNOWLEDGEGRAPG_TEMPLATE.format(knowledgegraph=graph_data)
            
            if excel_data:
                excel_data_prompt = DATA_INFO_TEMPLATE.format(data=excel_data)
                
        if knowledge:
            knowledge_prompt = format_knowledge_to_source_and_content(knowledge)
        else:
            knowledge_prompt = []

        
        
        snippets = []
        references = {}
        for k in knowledge_prompt:
            snippets.append(KNOWLEDGE_SNIPPET.format(source=k['source'], content=k['content']))
            references[k['source']] = k['content']
        knowledge_prompt = ''
        if snippets:
            knowledge_prompt = KNOWLEDGE_TEMPLATE.format(knowledge='\n\n'.join(snippets))

        #logger.info(f"材料中出现关键信息: {keyword_prompt}")


        base_info_prompt = BASE_INFO_TEMPLATE.format(
            current_time=get_current_time(),
            three_month=get_three_month_ago(),
            last_year=get_last_year(),
            current_year=get_current_year()
        )


        if knowledge_prompt:
            if messages and messages[0][ROLE] == SYSTEM:
                if isinstance(messages[0][CONTENT], str):
                    messages[0][CONTENT] += '\n\n' + knowledge_prompt + '\n\n'
                else:
                    assert isinstance(messages[0][CONTENT], list)
                    messages[0][CONTENT] += [ContentItem(text='\n\n' + knowledge_prompt + '\n\n' )]
            else:
                messages = [Message(role=SYSTEM, content=f"{DEFAULT_SYSTEM_MESSAGE}\n\n{knowledge_prompt}\n\n{knowledge_graph_prompt}\n\n {excel_data_prompt}\n\n{base_info_prompt}"),
                            messages[-1]]
        self.source = references

        #logger.info(f'最后提示词:{messages[0][CONTENT]}')
        return messages
    



        
    
    def _run_openai_format(
        self,
        messages: List[Message],
        lang: Literal['en', 'zh'] = 'zh',
        knowledge: str = '',
        **kwargs
    ) -> Iterator[str]:
        """Q&A with RAG and tool use abilities in OpenAI format.

        Args:
            knowledge: If an external knowledge string is provided,
              it will be used directly without retrieving information from files in messages.

        """
        # 使用与 _run 相同的逻辑
        new_messages = self._prepend_knowledge_prompt(messages=messages, lang=lang, knowledge=knowledge, **kwargs)
        #logger.info(f'new_messages:{new_messages}')

        chunk_id = f"chatcmpl-{uuid.uuid4().hex}"
        created = int(time.time())
        model = "xmtelecom"
        # 发送obs帧 - 检查是否有实质性的知识库内容
        # no_response = True #上线前改True
        if bool(self.source):
            #no_response = False 
            obs_chunk  = {
                    "id": chunk_id,
                    "object": "chat.completion.observation",
                    "created": created,
                    "model": model,
                    "choices": [{
                        "index": 0,
                        "delta": {"content": json.dumps(self.source,ensure_ascii=False)},
                        "finish_reason": None
                    }]
                }
            yield f"data: {json.dumps(obs_chunk, ensure_ascii=False)}\n\n"
        else:
            logger.info('Skipping obs chunk due to insufficient content')

        

        # 调用父类的 _run 方法，但转换输出格式为 OpenAI 流式格式
        chunk_id = f"chatcmpl-{uuid.uuid4().hex}"
        model = "xmtelecom"

        # 发送开始帧
        start_chunk = {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model,
            "choices": [{
                "index": 0,
                "delta": {"role": "assistant"},
                "finish_reason": None
            }]
        }
        yield f"data: {json.dumps(start_chunk, ensure_ascii=False)}\n\n"




        # 主要回答生成
        try:
            # 生成主要回答，不传递prev_full_text避免重复
            yield from self.call_llm_with_messages(chunk_id=chunk_id,
                                                   model=model,
                                                   messages=new_messages,
                                                   lang='zh')

        except Exception as e:
            logger.error(f"Error in main response generation: {e}")
            # 发送错误消息给用户
            error_chunk = {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model,
                "choices": [{
                    "index": 0,
                    "delta": {"content": "\n抱歉，生成回答时遇到问题，请稍后重试。"},
                    "finish_reason": None
                }]
            }
            yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
        

        # 发送结束帧
        final_chunk = {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }]
        }
        yield f"data: {json.dumps(final_chunk, ensure_ascii=False)}\n\n"
        #yield "data: [DONE]\n\n"


    def call_llm_with_messages(self, chunk_id, model, messages: List[Message], lang, **kwargs):
        """
        调用LLM生成流式响应

        Args:
            prev_full_text: 之前的文本内容（避免重复输出时使用）
            is_supplement: 是否为补充说明
        """
        for message_batch in super()._run(messages=messages, lang=lang, **kwargs):
            if message_batch and message_batch[-1]:
                content = message_batch[-1].get(CONTENT, '')
                if content:
                    if isinstance(content, str):
                        text_content = content
                    else:
                        # 处理 ContentItem 列表
                        text_content = ""
                        for item in content if isinstance(content, list) else []:
                            if hasattr(item, 'text'):
                                text_content += item.text

                    
                    self.full_text = text_content
                    self.sources = self._extract_content_ref(text_content)
                    delta = {"content": text_content}
                    chunk = {
                        "id": chunk_id,
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": model,
                        "choices": [{
                            "index": 0,
                            "delta": delta,
                            "finish_reason": None
                        }]
                    }
                    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        # 带索引：
        
        if self.sources:
            references = [k['reference'] for k in self.knowledge_data if k['url'] in self.sources and k['reference'] is not None]
            reference = []
            for k in references:
                item = k.split('\n')
                for i in item:
                    if i not in reference:
                        reference.append(i)
            self.supp_text = "\n\n".join(reference)
            if len(reference):
                delta = {"content": f'{self.full_text}\n\n**参考出处**\n\n{self.supp_text}'}
            else:
                delta = {"content": f'{self.full_text}\n\n'}
            #delta = { "content": f'{self.full_text}',"source": reference}
            
            chunk = {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model,
                "choices": [{
                    "index": 0,
                    "delta": delta,
                    "finish_reason": None
                }]
            }
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

    def _extract_content_ref(self, full_text: str) -> List[str]:
        """正则表达式提取所有的字符串
            例如 [来源: [3](3)] 你应该得到 [3]

            [来源: [2](2), [7](7),[34](34),[46](46),[graph_chunk](graph_chunk), +more)]。
            得到 [2,7,34,46,graph_chunk]

            [来源: [doc_12579] 得到 doc_12579
        """
        import re

        result = []
        seen = set()

        # 模式1: 匹配 [来源: [内容](链接)] 格式
        pattern1 = r'\[来源:\s*\[([^\]]+)\]\([^)]+\)\]'
        matches1 = re.findall(pattern1, full_text)

        # 模式2:
        pattern2 = r'(?:doc_\d{5}|\d{5})'
        matches2 = re.findall(pattern2, full_text)

        # 合并所有匹配结果
        all_matches = matches1 + matches2

        # 去重并保持顺序
        for match in all_matches:
            if match not in seen:
                seen.add(match)
                result.append(match)

        return result