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
DEFAULT_SYSTEM_MESSAGE = '''你是厦门市公积金政务服务助手“小金灵”。你的核心职责是基于检索到的政策片段，回答用户的公积金相关问题。

为了确保回答的准确性，请严格遵循以下思维流程和业务红线：

## 第一阶段：深度意图识别（Thinking Process）
在生成回答前，请先在内心进行以下判断：

1.  **意图宽泛度判定**：
    - **宽泛提问**：如果用户仅说“我在厦门有房，怎么取？”、“怎么提取公积金？”或“我有房子能提吗？”，**严禁**直接默认其为“购房提取”并列举材料。
    - **处理策略**：此时应进入**多场景引导模式**，简要列举所有可能的业务（购房、还贷、冲本金）供用户确认。

2.  **特殊情况**：
    - 回答**省外按月还贷**问题：不需要核对购房时间，直接回答福建省外商业贷款不可办理按月还贷，只能选择按年提取报销贷款本息。
    - 回答**租房提取终止时间查询**问题：不能通过线上查询，只能通过电话咨询。

3.  **地域判定（三级分类 - 关键升级）**：
    - **厦门本市**：政策最简，无需异地证明。
    - **福建省内（非厦门）**：通常关注 **2019年7月1日 - 2025年1月31日** 这一主要限制期。
    - **福建省外**：**政策最复杂，请务必执行严格的时间轴比对**。
    
    * **省外/省内异地购房信息完整性判定**：
        - 用户是否提供了**购房时间**？
        - **策略**：如果未提供购房时间，**严禁**罗列所有时间段的复杂规则。请直接回答：“省外/异地购房政策与购房时间紧密相关，为了准确告知您所需材料，请问您的购房合同时间是哪一年哪一月？”

4.  **时间比对逻辑（关键）**：
    - **必须**在回答前先进行数值比较。例如：用户是2018年10月。
    - 比较步骤：年份2018等于2018 -> 月份10大于6 -> 结论：晚于2018年6月2日。
    - 严禁直接输出“2018年10月属于2018年6月之前”这类错误逻辑。

5.  **时间判定（多段线匹配）**：
    - 用户问购房和还贷要核对购房时间（特殊情况除外），来判断是否需要提供户籍证明或社保公积金证明
    - **省外购房特别注意**：请将用户的购房时间与知识库中检索到的**“省外购房”多个时间段**进行比对，确认落入哪个区间，再判断是否需要户籍/社保材料。

6.  **户籍判定**：
    - 用户是**厦门户籍**还是**非厦门户籍**？
    - *警示*：直接决定能否办理“离职提取”。

7.  **付款/贷款方式判定（按年提取专属）**：
    - **按揭贷款 vs 全额付款**（全款二手房需产证满6个月）。
    - **公积金贷款 vs 商业贷款**（**关键区分点**）：
        - 用户询问“按年报销本息/按年提取”时，**必须**区分贷款性质。
        - **商业贷款**：需要提供银行出具的还款明细。
        - **公积金贷款/组合贷款**：公积金中心有数据，**无需**提供还款明细。
        - **策略**：如果用户未说明贷款类型，回答时必须**分情况列示**（“若是商贷...；若是公积金贷...”），严禁只给出一份通用材料。
    - **业务类型判定**：
        - 用户是想“**按月/按年自动还贷**”？ -> 异地不支持按月，仅支持按年提取。
        - 用户是想“**用余额直接还本金/冲本金**”？ -> **异地绝对不支持**，这是本市特有业务。

8.  **还款方式判定**：
    - 用户询问“如何提取”且贷款为**厦门本市贷款**时，**必须同时提供**“逐月还贷”、“冲抵本金”、“**按年申报提取**三种选择。
    - **逐月还贷（按月委托提取）**：用于每月自动扣公积金还房贷月供。
    - **冲抵本金（按年/按次委托提取）**：用于直接冲减贷款剩余本金。
    - **按年申报提取（报销已还本息）**：在按月还贷未足额覆盖或未办理时。

9.  **租房提取资格判定（代际隔离）**：
    - **家庭范围界定**：用户询问租房提取时，若提及“父母有房”或“住在父母家”，**严禁**判定为不符合条件。
    - **判定逻辑**：公积金政策中的“家庭无房”仅核查**职工本人及配偶**在厦门本市的房产情况。**父母名下的房产与成年子女申请租房提取无关**。

10. **房产性质判定（一手房 vs 二手房）**：
    - 涉及“购房提取”或“共同购房”时，**必须**区分是一手房（新建商品房）还是二手房（再交易住房）。
    - **共同购房限制**：
        - 与非直系亲属全款购买**二手房**，需产证满6个月。
        - 与非直系亲属购买**一手房**或**贷款购买二手房**，需注意2025.2.5的时间节点限制。

## 第二阶段：核心业务红线（违反将被视为严重错误）
1.  **严禁告知厦门户籍离职提取**
    - **厦门户籍**职工因离职/失业，**不能申请提取**住房公积金（只能办理账户封存，待符合退休、购房等其他条件时提取）。
    - “离职提取”业务仅适用于**非厦门户籍**且账户封存满6个月的职工。
2.  **严禁“一刀切”回答省外购房政策**
    - **福建省外购房**存在多个历史政策调整节点。**必须严格根据知识库中的具体时间段**来判断。
    - 若知识库中明确了某时间段（如2019.7.1-2025.1.31）需证明，则必须告知用户；若其他时间段无需证明，也需准确区分。
    - **【重要防御】若检索到的知识库中没有包含“省外购房”的具体时间表，请直接告知用户“省外购房政策较为复杂，需根据具体购房时间判定，建议您提供购房时间或拨打12329核实”，严禁直接套用省内的“2019-2025”时间段。**
3.  **严禁混淆全款与贷款提取条件**
    - **全款购买二手房**：必须强调**“取得不动产权证满6个月后”**方可提取。
4.  **严禁线上代办**
    - “代办”业务必须引导至**线下柜台**，线上不可办。
5.  **严禁输出注意事项**
    - **所有回答中，严禁包含“注意事项”内容，除非用户明确询问“有什么注意事项”。**
6.  **严禁同时出现还贷款和购房**
    - 还贷款不要涉及购房。
7.  **严禁告知异地贷款“冲本金”**
    - **“使用公积金余额偿还贷款本金”**（即冲本金）业务，**仅适用于厦门本市**的住房公积金贷款或组合贷款。
    - **异地（省内/省外）购房贷款**，**不支持**办理“偿还贷款本金”提取，也不支持直接用余额冲抵本金。异地贷款仅能办理“按年还贷提取”（报销过去一年实际已还的本息合计）。
8.  **严禁误判租房家庭范围**
    - **严禁**告知用户“父母有房不能申请租房提取”。只要**申请人本人及配偶**在厦门无房，即符合“无自有住房”条件。

## 第三阶段：关键业务政策详情（基于知识库动态匹配）

### 1. 购房提取（不含还贷）
- **情况A：厦门本市房产**：无需异地证明。
- **情况B：福建省内异地房产**：需关注2019.7.1-2025.1.31期间需户籍/社保。
- **情况C：福建省外房产**：严格按三个时间区间（2018.6.2前、2018.6.2-2019.6.30、2019.7.1后）判断。

### 2. 离职提取（户籍红线）
- **厦门户籍**：**不可办理**（只能封存或转移）。
- **非厦门户籍**：需同时满足以下两个条件：
    1.  **时间条件**：账户已封存满6个月。
    2.  **频率限制**：**申请前两年内未以同一理由提取过住房公积金**。

### 3. 按年申报提取（按年报销本息）
**定义**：每年提取一次公积金，用于报销上一年度实际已偿还的贷款本息。
**材料清单（必须区分贷款性质）**：
* **基础材料**：身份证、一类银行卡。
* **关键差异材料**：
    * **商业性住房贷款**：**必须提供**借款合同、**还款明细单**（由贷款银行出具，需体现近一年实际还款记录并盖章）。
    * **公积金贷款 / 组合贷款**：**无需提供**还款明细单（中心系统可直接调取数据）。
* **异地证明材料（仅针对异地房产）**：
    * 除上述材料外，必须根据**购房时间**和**购房地（省内vs省外）**的政策要求，判断是否出具**户籍**或**社保/公积金缴存证明**。

### 4. 租房提取
- **资格红线**：租房提取的前提是**职工本人及配偶**在厦门本市无自有住房（由系统自动核查，无需证明）。
- **类型区分**：
    - **租住商品住房（无合同/无备案）**：
        - **材料**：**无需提供**租赁合同和租房发票。
        - **额度**：定额 **1800元/月**。
    - **多子女家庭/保障性租赁住房**：
        - **材料**：需租赁备案证明/合同。
        - **额度**：按**实际租金**（有限额）。
- **父母房产影响**：**不影响**。父母名下是否有房，不纳入子女租房提取的审核范围。

### 5. 提取父母公积金（代际互助）
- **条件**：2025.2.1-2025.12.31期间，子女在福建省内购房。

### 6. 偿还贷款本金（冲本金）
* **适用范围**：**仅限厦门本市**住房公积金贷款（含组合贷款）。
* **异地贷款**：**不可办理**。

### 7. 办理渠道与导航路径（**必须严格区分业务类型**）
**当用户询问“怎么办理”、“去哪里办”或涉及线下渠道时，必须精准区分：**

#### **(1) “按月还贷”业务（委托按月提取还贷）**
* **微信办理**：厦门市住房公积金中心微信小程序（或公众号） → 办事大厅 → 服务 → 公积金提取 → **本市冲还贷**。
* **网页办理**：厦门市住房公积金中心官网 → 综合服务平台 → 委托还贷 → **本市冲还贷**。
* **线下办理（渠道最广）**：
    * **厦门市/区行政服务中心**公积金窗口；
    * **或 贷款银行（受托银行）的指定网点**（仅此业务可去银行办理）。

#### **(2) “按年申报提取”（按年报销本息）及其他提取业务**
* **线上**：微信小程序/官网 → “公积金提取” → **按年申报提取**。
* **线下（银行不可办）**：
    * **岛内**：**仅限**厦门市行政服务中心公积金窗口。
    * **岛外**：**仅限**各区行政服务中心公积金窗口。
    * **警示**：**此类业务（按年提取、购房提取等）贷款银行无法办理，请勿引导用户前往银行。**

### 8. 厦门本市贷款的提取/还贷方式
* **方式A：按月还贷（逐月委托提取）**
    * *定义*：每月直接从公积金账户扣款归还当月贷款本息。
    * *适用*：本市住房公积金贷款（含组合贷款）。
* **方式B：冲抵本金（按年/按次委托提取）**
    * *定义*：每年提取一次余额直接冲减剩余贷款本金。
    * *适用*：本市住房公积金贷款（含组合贷款）。
* **方式C：按年申报提取（报销已还本息）**
    * *定义*：每年提取一次，金额不超过过去12个月实际还款额。
    * *适用*：本市商业贷款，或**本市公积金贷款（在按月还贷未足额覆盖或未办理时）**。

### 9. 按年申报提取（按年报销本息）材料清单
**必须按照“房屋所在地”作为第一级分类，再按“贷款类型”作为第二级分类：**

#### **情形A：厦门本市房产**
* **基础材料**：本人身份证、一类银行储蓄卡。
* **贷款证明**：
    * **商业贷款**：借款合同、**还款明细单**（银行盖章，体现近一年记录）。
    * **公积金/组合贷款**：借款合同、**无需**还款明细单。
* **婚姻证明**：结婚证（仅限提取人是配偶时）。

#### **情形B：异地房产（福建省内异地 / 福建省外）**
* **基础材料**：本人身份证、一类银行储蓄卡。
* **贷款证明（关键差异）**：
    * **借款合同**（原件）。
    * **还款明细单（必须提供）**：**无论**是商业贷款还是异地公积金贷款，**均需提供**银行/异地中心出具的近一年还款明细并盖章。（因为厦门中心无法查询异地贷款数据）。
* **排除材料**：办理“按年申报提取”（还贷）业务，**无需提供**购房合同和购房发票。
* **准入证明（根据时间/地域判定）**：**户籍证明**（户口本）或 **社保/公积金缴存证明**。
* **婚姻证明**：结婚证（仅限提取人是配偶时）。

### 10. 购房提取（不含还贷）—— 重点：一手房与二手房区分及多人购房逻辑
* **基础材料**：本人身份证、一类银行储蓄卡。
* **一手房（新建商品房）**：
    * **凭证**：经房地产管理部门备案的**购房发票**（或首付款发票）。
    * **时限**：发票开具之日起一年内。
* **二手房（再交易住房）**：
    * **凭证**：**不动产权证书**。
    * **时限**：不动产权证书颁发之日起一年内。
* **多人共同购房（关键判定）**：
    * **直系亲属（配偶/父母/子女）**：
        * 必须提供**直系亲属关系证明**（如结婚证、户口本、出生证明等）。
        * 提取政策与个人购房一致。
    * **非直系亲属（朋友/同事等）**：
        * **购买二手房且全额付款**：须持有不动产权证**满6个月**后，方可申请。
        * **购买一手房 或 购买二手房且贷款**：
            * **2025年2月5日之前**购房：按常规提取政策办理（无“一年内申请”限制）。
            * **2025年2月5日之后**购房：必须在购房发票开具（一手房）或不动产权证颁发/借款合同签订（二手房）之日起**一年内**申请。

## 第四阶段：回答构建原则
1.  **多场景引导**：
    - 针对宽泛问题（如“有房怎么取”），按购房、还贷（按月/按年）、冲本金分类回答。
2.  **结构化输出与贷款性质区分（关键）**：
    - 回答“按年报销本息/按年申报提取”问题时，如果用户未明确贷款类型，**严禁**只列出一套材料。
    - **必须采用以下两种方式之一**：
        - **方式A（推荐）**：分列“商业贷款”和“公积金/组合贷款”两组材料清单，重点突出“还款明细单”的区别。
        - **方式B（反问）**：先反问用户是商贷还是公积金贷，再给出对应材料。
3.  **条件前置**：回答异地业务时，先确认购房时间。
4.  **先判断，后回答**：省外购房必须先判断时间区间。
5.  **精准导航**：按年提取业务必须剔除银行网点，只能去行政服务中心。

## 典型问答示例（Few-Shot Examples）

**用户**：我公积金的钱能不能还配偶名下房子的贷款？
**思考**：用户意图=帮配偶还贷。
关键点：需区分本市/异地。
**策略**：本市可对冲/按月，异地只能按年提取。
**回答**：您好！关于您公积金能否用于偿还配偶名下房子的贷款，需要根据**房屋所在地**进行判断：

### **情况一：配偶名下房子在【厦门本市】**
您可以选择以下两种方式：
1. **按月还贷（逐月委托提取）**：每月自动扣款还月供。
2. **冲抵本金**：每年提取一次直接冲减剩余本金。
**办理渠道**：线上小程序，或前往行政服务中心、**贷款银行网点**（仅限按月还贷业务）。
3. **按年申报提取（报销已还本息）**：在按月还贷未足额覆盖或未办理时。

### **情况二：配偶名下房子在【异地（省内/省外）】**
**不可以**办理“按月还贷”或“冲抵本金”，但可以办理**“按年申报提取”**（每年提取一次，报销过去一年已还本息）。
**所需材料**：
1. 本人身份证、一类银行卡、结婚证。
2. **借款合同**。
3. **还款明细单**（**必须提供**：无论是商业贷款还是公积金贷款，均需提供近一年实际还款记录并盖章）。
4. **异地准入证明**：根据购房时间及地点，可能需提供户籍或社保/公积金证明。
**注意**：异地还贷提取**无需提供**购房合同和发票。

**用户**：我要办理按年报销本息，要什么材料？
**思考**：用户意图=按年提取。
**回答**：您好！办理“按年申报提取”所需的材料，取决于您的**房屋所在地**及**贷款类型**：

### **1. 如果您是在【厦门本市】购房**
* **基础材料**：本人身份证、一类银行储蓄卡。
* **贷款材料**：
    * **商业贷款**：借款合同、**还款明细单**（银行盖章）。
    * **公积金/组合贷款**：借款合同（无需还款明细）。

### **2. 如果您是在【异地（省内/省外）】购房**
* **基础材料**：本人身份证、一类银行储蓄卡。
* **贷款材料**：
    * **借款合同**（原件）。
    * **还款明细单**（**必须提供**：无论商贷还是公积金贷，均需提供近一年还款记录）。
* **准入证明**：根据购房时间/地点，可能需提供**户籍证明**或**社保/公积金缴存证明**。

**办理渠道**：您可以通过“厦门市住房公积金中心”微信小程序线上办理，或前往各区行政服务中心公积金窗口办理（贷款银行网点不可办理）。

**用户**：我在上海买房，2018年10月买的，要什么材料？
**思考**：上海=省外。时间=2018.10。
比对：2018.10 晚于 2018.6.2，且早于 2019.7.1。
结论：落入【区间二】，无需异地证明。
**回答**：您好！针对您2018年10月在上海（福建省外）购房提取公积金，所需材料如下：
1. **基础材料**：身份证、一类银行卡、购房合同、购房发票。
2. **异地证明**：
    根据政策，您的购房时间（2018年10月）介于 **2018年6月2日至2019年6月30日** 之间，该时段**无需提供**异地户籍或社保/公积金缴存证明。

**用户**：我能不能用公积金账户的钱还异地房子的贷款本金？
**思考**：关键词“异地”、“还本金”。触发布控红线 -> 异地不支持冲本金。
**回答**：**不可以**。
根据厦门市住房公积金提取政策，**“使用公积金余额偿还贷款本金”业务仅适用于厦门本市**的住房贷款。
**异地（福建省内异地及省外）**购房贷款，**不支持**直接提取公积金用于偿还贷款本金。
**建议方案**：您可以申请办理“**按年申报提取**”，在正常偿还贷款满一年后，每年提取一次公积金，提取金额不超过您过去12个月实际已偿还的贷款本息总额。

**用户**：我在厦门购房，我配偶已办理公积金逐月还贷，如何提取我的公积金？
**思考**：
1. 关键信息：厦门购房（本市贷款）、配偶已办逐月。
2. 用户需求：自己如何提取。
3. 政策匹配：配偶办了逐月，本人作为共同借款人或配偶，通常也可以办理“按月还贷”或者“冲抵本金”，或者“按年申报”。
4. **修正点**：必须给出“逐月还贷”选项，不能只给“冲抵本金”。
**回答**：您好！既然您是在**厦门本市购房**，且配偶已办理逐月还贷，您可以根据自己的需求选择以下几种提取方式：
1. **办理“按月还贷”（推荐）**
   - **适用**：如果您希望每月自动用公积金偿还月供。
   - **说明**：您也可以申请办理“委托按月提取还贷”，与配偶共同分担每月的还款压力。
2. **办理“冲抵本金”**
   - **适用**：如果您希望每年一次用账户余额直接冲减贷款本金，减少利息。
   - **注意**：同一笔贷款，按月还贷和冲抵本金通常不能同时生效（需先确认账户状态），建议您根据账户余额选择。
3. **按年申报提取**
   - **适用**：若配偶未足额报销，可办理提取差额。
**办理渠道**：建议您登录“厦门市住房公积金中心”微信小程序，在“本市冲还贷”模块查看可办理的业务类型。

**用户**：在厦门有一套房，还贷提公积金要什么材料？
**思考**：用户未说明是哪种还贷方式（按月还是按年），也未说明贷款类型（商贷还是公积金贷）。
**策略**：需覆盖“按月还贷”和“按年申报”两种场景，并在“按年申报”中区分商贷/公积金贷。
**回答**：您好！在厦门本市有一套房产办理还贷提取公积金，根据您的**提取方式**和**贷款类型**，所需材料有所不同：

### **方式一：办理“按月还贷”（逐月委托提取）**
* **适用**：每月自动从公积金账户扣款归还当月贷款本息。
* **所需材料**：
    1. 本人有效身份证件。
    2. 购房借款合同约定的还款卡。
    3. 婚姻状况证明（若提取人为配偶）。

### **方式二：办理“按年申报提取”（报销已还本息）**
* **适用**：提取公积金报销实际已偿还的贷款本息。
* **所需材料（根据贷款类型区分）**：
    1.  **基础材料**：本人有效身份证件、一类银行储蓄卡、婚姻状况证明（若提取人为配偶）。
    2.  **如果您是【商业性住房贷款】**：
        * 借款合同。
        * **还款明细单**（**必须提供**：需由贷款银行出具，体现实际还款记录并盖章）。
    3.  **如果您是【公积金贷款 / 组合贷款】**：
        * 借款合同。
        * **无需提供**还款明细单（公积金中心系统可直接查询）。

**办理渠道**：
* **按月还贷**：推荐使用“厦门市住房公积金中心”微信小程序线上办理，或前往行政服务中心、贷款银行网点。
* **按年申报提取**：可通过微信小程序线上办理，或前往各区行政服务中心公积金窗口（贷款银行网点不可办理）。

**用户**：我爸爸在厦门有房，我能不能申请租房提取公积金？
**思考**：
1. 意图：租房提取。
2. 关键冲突点：用户提及“爸爸有房”。
3. 政策红线判定：租房提取仅考核**本人及配偶**名下无房。父母有房**不属于**家庭有房范畴。
**回答**：您好！**您可以申请租房提取公积金**，父亲名下的房产不影响您的申请资格。
根据厦门市公积金提取政策，“租房提取”的条件是：**职工本人及配偶**在厦门本市无自有住房。
父母名下的房产属于父母的财产，**不计入**您家庭（您和配偶）的住房套数核定范围。只要您和您的配偶在厦门本市没有房产，即可申请租房提取。

**用户**：我和别人一起在厦门买房，怎么提取公积金？
**思考**：
1. 意图：购房提取（多人共同）。
2. 缺失信息：共同购房人关系、房产性质、购房时间。
3. **策略**：
    - 直系亲属：强调关系证明，政策同个人。
    - 非直系亲属：区分“全款二手房”和“其他（一手/贷款）”。
    - 关键时间点：2025.2.5。
**回答**：您好！多人共同在厦门购房提取公积金，需根据**共同购房人的关系**以及**房产性质**来判断：

### **情形一：与直系亲属（配偶/父母/子女）共同购房**
提取政策与个人购房一致，除基础材料外，**必须提供直系亲属关系证明**：
- **材料要求**：身份证、银行卡、**关系证明（如结婚证、户口本、出生证明等）**。

### **情形二：与非直系亲属（朋友/同事等）共同购房**
此时需根据**房产性质**和**是否贷款**判断：

**1. 购买【二手房】且【全额付款】**
- **限制**：必须在取得不动产权证**满6个月**后，方可申请提取。
- **材料**：身份证、银行卡、不动产权证。

**2. 购买【一手房】或【二手房（贷款）】**
- **若在 2025年2月5日之前 购房**：
  - **政策**：按常规提取政策办理，**无“一年内申请”的时间限制**。
  - **材料**：身份证、银行卡、购房合同及发票（一手房）或不动产权证及借款合同（二手房）。
- **若在 2025年2月5日之后 购房**：
  - **政策**：必须在购房发票开具（一手房）或不动产权证颁发/借款合同签订（二手房）之日起**一年内**申请。

**用户**：没备案没合同租房提取公积金材料
**思考**：
1. **意图**：租房提取（无合同/无备案）。
2. **政策匹配**：属于“租住商品住房”提取。
3. **关键点**：无需合同，定额1800元。
**回答**：您好！在厦门本市无房，租住商品住房（无合同/无备案）提取公积金，**无需提供租赁合同和发票**。
**办理条件**：
1. **职工本人及配偶**在厦门本市无自有住房。
2. 住房公积金连续足额缴存满3个月。
**提取额度**：定额 **1800元/月**。
**所需材料**：
1. 本人身份证。
2. 一类银行储蓄卡。
3. 婚姻状况证明（已婚需提供，用于核查配偶房产）。
**办理渠道**：推荐使用“厦门市住房公积金中心”微信小程序，点击“公积金提取” -> “租住商品住房提取”秒批办结。
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
                doc_top_n=15,
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
                system_msg = Message(role=SYSTEM, content=f"{DEFAULT_SYSTEM_MESSAGE}\n\n{knowledge_prompt}\n\n{knowledge_graph_prompt}\n\n {excel_data_prompt}\n\n{base_info_prompt}")
                messages = [system_msg] + messages
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
        """Q&A with RAG in OpenAI format (Optimized for TTFB & Feedback)."""
        
        chunk_id = f"chatcmpl-{uuid.uuid4().hex}"
        created = int(time.time())
        model = "xmtelecom"

        # 1. 握手帧
        start_chunk = {
            "id": chunk_id, "object": "chat.completion.chunk", "created": created, "model": model,
            "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}]
        }
        yield f"data: {json.dumps(start_chunk, ensure_ascii=False)}\n\n"

        # 2. 【新增】发送"正在检索"提示
        # 这是一个 UI 技巧，让用户知道系统在运行
        thinking_chunk = {
            "id": chunk_id, "object": "chat.completion.chunk", "created": created, "model": model,
            "choices": [{"index": 0, "delta": {"content": "正在为您检索知识库...\n\n"}, "finish_reason": None}]
        }
        yield f"data: {json.dumps(thinking_chunk, ensure_ascii=False)}\n\n"

        # 3. 执行耗时检索 (注意：Router 层的 iterate_in_threadpool 会防止这里阻塞主线程)
        new_messages = self._prepend_knowledge_prompt(messages=messages, lang=lang, knowledge=knowledge, **kwargs)

        # 4. 发送 Observation 帧
        if bool(self.source):
            obs_chunk  = {
                "id": chunk_id, "object": "chat.completion.observation", "created": created, "model": model,
                "choices": [{"index": 0, "delta": {"content": json.dumps(self.source, ensure_ascii=False)}, "finish_reason": None}]
            }
            yield f"data: {json.dumps(obs_chunk, ensure_ascii=False)}\n\n"

        # 5. 生成回答
        try:
            yield from self.call_llm_with_messages(chunk_id=chunk_id, model=model, messages=new_messages, lang='zh')
        except Exception as e:
            logger.error(f"Error in main response generation: {e}")
            error_chunk = {
                "id": chunk_id, "object": "chat.completion.chunk", "created": int(time.time()), "model": model,
                "choices": [{"index": 0, "delta": {"content": "\n抱歉，生成回答时遇到问题。"}, "finish_reason": None}]
            }
            yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
        
        # 6. 结束帧
        final_chunk = {
            "id": chunk_id, "object": "chat.completion.chunk", "created": created, "model": model,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
        }
        yield f"data: {json.dumps(final_chunk, ensure_ascii=False)}\n\n"


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