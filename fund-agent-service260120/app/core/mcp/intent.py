"""
用户意图识别和问题改写MCP工具
用于公积金领域的智能意图分类和问题优化
"""

from mcp.server.fastmcp import FastMCP
from datetime import datetime
import json5
import re
import jieba
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("intent_recognition")

@dataclass
class IntentResult:
    """意图识别结果"""
    first_level: str
    second_level: str
    third_level: str
    confidence: float
    action: str
    rewritten_query: str
    needs_clarification: bool          # 新增：是否需要澄清
    clarification_question: str        # 新增：反问内容
    

class ProvidentFundIntentRecognizer:
    """公积金意图识别器"""

    def __init__(self):
        self.intent_taxonomy = self._build_intent_taxonomy()
        self.keyword_mappings = self._build_keyword_mappings()
        self.synonym_dict = self._build_synonym_dict()
        self.pattern_rules = self._build_pattern_rules()
        self.completeness_rules = self._build_completeness_rules()  # 新增：完整性规则

    def _build_intent_taxonomy(self) -> Dict:
        """构建公积金意图分类体系"""
        return {
            "公积金缴存业务": {
                "缴存管理": {
                    "缴存对象": ["单位职工", "灵活就业人员", "个人自愿缴存", "企业员工", "机关事业单位", "缴存人"],
                    "缴存基数与比例": ["缴存基数", "缴存比例", "基数上限", "比例范围", "调整基数"],
                    "缴存方式（单位/个人）": ["单位缴存", "个人缴存", "代扣", "自缴", "汇缴"],
                    "缴存变更（增员/减员）": ["增员", "减员", "新增缴存", "停止缴存", "人员变更"],
                    "补缴与缓缴规定": ["补缴", "缓缴", "补缴流程", "缓缴条件", "补缴费用"],
                    "缴存纠纷处理": ["缴存纠纷", "未缴", "少缴", "投诉", "维权", "缴存问题"]
                },
                "缴存相关": {
                    "缴存明细查询": ["缴存明细", "缴费记录", "查询缴存", "缴存历史"],
                    "缴存证明开具": ["缴存证明", "开具证明", "公积金证明", "提取证明"],
                    "汇缴托收办理": ["汇缴", "托收", "自动汇缴", "委托缴存"],
                    "退费办理": ["退费", "退款", "返还", "多缴退费", "错缴返还"],
                    "重复缴存处理": ["重复缴存", "多地缴存", "双重缴存", "缴存冲突"]
                },
                "缴存办理指南": {
                    "单位缴存登记": ["单位开户", "缴存登记", "单位注册", "开户流程"],
                    "个人自愿缴存申请": ["个人开户", "自愿缴存", "个人缴存申请"],
                    "缴存基数调整办理": ["基数调整", "调整缴存基数", "基数变更"],
                    "单位缴存信息变更": ["单位信息变更", "缴存信息修改", "单位名称变更"]
                }
            },
            "公积金提取业务": {
                "提取类型": {
                    "购房提取": ["购房提取", "买房提取", "购房取公积金", "买房提公积金"],
                    "租房提取": ["租房提取", "租房取公积金", "租房提公积金"],
                    "离职提取": ["离职提取", "辞职提取", "失业提取", "外地户籍离职"],
                    "退休提取": ["退休提取", "离休提取", "退休取公积金"],
                    "代际互助提取": ["代际互助", "父母提取", "子女提取", "亲属互助"],
                    "其他提取（出境/大病等）": ["出境提取", "大病提取", "残疾提取", "低保提取", "死亡提取"]
                },
                "提取管理": {
                    "提取条件": ["提取条件", "提取资格", "符合什么条件", "提取要求"],
                    "提取额度": ["提取额度", "能提多少", "提取上限", "提取金额"],
                    "提取频次": ["提取次数", "多久提一次", "提取频率"],
                    "提取限制": ["提取限制", "不能提取", "提取禁区", "限制条件"]
                },
                "提取办理指南": {
                    "提取材料准备": ["提取材料", "需要什么材料", "材料清单", "证明材料"],
                    "线上提取办理": ["线上提取", "微信提取", "官网提取", "支付宝提取"],
                    "线下提取办理": ["线下提取", "窗口提取", "银行提取", "现场提取"],
                    "提取进度查询": ["提取进度", "查询提取", "提取状态", "办理进度"],
                    "提取到账查询": ["到账时间", "提取到账", "多久到账", "到账查询"]
                }
            },
            "公积金贷款业务": {
                "贷款申请": {
                    "贷款条件": ["贷款条件", "贷款资格", "申请条件", "贷款要求"],
                    "贷款额度计算": ["贷款额度", "能贷多少", "额度计算", "贷款上限"],
                    "贷款期限规定": ["贷款期限", "还款年限", "贷款年限", "期限上限"],
                    "贷款利率标准": ["贷款利率", "利率多少", "利息标准", "利率调整"],
                    "贷款申请材料": ["贷款材料", "申请材料", "材料清单", "贷款证明"]
                },
                "贷款管理": {
                    "还款方式": ["还款方式", "等额本息", "等额本金", "还款选择"],
                    "还款额度调整": ["还款调整", "调整月供", "额度变更", "还款额修改"],
                    "提前还款规定": ["提前还款", "提前还贷", "提前结清", "部分还款"],
                    "贷款展期办理": ["贷款展期", "展期申请", "延长贷款期限"],
                    "贷款变更（还款账户/方式）": ["还款账户变更", "变更还款方式", "账户修改"]
                },
                "贷款办理指南": {
                    "贷款申请流程": ["贷款流程", "申请流程", "办理步骤", "贷款手续"],
                    "贷款审批时限": ["审批时间", "多久审批", "审批时限", "审核时间"],
                    "异地贷款办理": ["异地贷款", "外地买房贷款", "跨省贷款", "省内异地贷款"],
                    "商转公贷款办理": ["商转公", "商业贷款转公积金", "商转公流程"],
                    "贷款进度查询": ["贷款进度", "查询贷款", "贷款状态", "审批进度"]
                }
            },
            "公积金账户管理业务": {
                "账户维护": {
                    "个人账户设立": ["账户设立", "开户", "个人账户开户", "新建账户"],
                    "账户封存与启封": ["账户封存", "封存账户", "启封", "账户解封"],
                    "账户信息变更": ["信息变更", "姓名变更", "身份证变更", "账户修改"],
                    "账户注销": ["账户注销", "销户", "注销公积金账户"],
                    "异地转移接续": ["异地转移", "转移公积金", "转入", "转出", "异地接续"]
                },
                "账户查询": {
                    "账户余额查询": ["余额查询", "查公积金余额", "账户余额", "余额多少"],
                    "账户状态查询": ["账户状态", "查询状态", "封存状态", "正常状态"],
                    "业务办理记录查询": ["办理记录", "业务记录", "查询历史", "操作记录"],
                    "个人缴存证明打印": ["打印缴存证明", "证明打印", "打印公积金证明"]
                },
                "账户办理指南": {
                    "单位账户管理": ["单位账户", "单位账户查询", "单位账户维护"],
                    "个人账户异地转入": ["异地转入", "转入公积金", "外地转入"],
                    "账户信息更正办理": ["信息更正", "账户纠错", "修改错误信息"],
                    "家庭共济账户绑定": ["家庭共济", "账户绑定", "家人绑定", "共济绑定"]
                }
            },
            "其他公积金政策": {
                "专项业务政策": {
                    "代际互助业务": ["代际互助政策", "互助提取规则", "亲属提取政策"],
                    "老旧住宅加装电梯提取": ["加装电梯提取", "电梯提取", "住宅电梯提取"],
                    "保障性住房相关公积金政策": ["保障房公积金", "保障性住房提取", "保障房贷款"]
                },
                "补充政策": {
                    "公积金政策法规解读": ["政策解读", "法规说明", "政策解释", "新规解读"],
                    "便民服务（上门/预约）": ["上门服务", "预约服务", "便民服务", "预约办理"],
                    "线上渠道操作指引": ["线上操作", "网厅操作", "小程序操作", "线上指南"],
                    "受托银行业务网点查询": ["银行网点", "经办银行", "网点查询", "银行地址"]
                }
            }
        }

        def _build_keyword_mappings(self) -> Dict:
            """构建公积金关键词映射"""
            return {
                # 同义词映射
                "公积金": ["住房公积金", "公积金账户", "住房公积金账户", "厦公积金"],
                "提取": ["支取", "提取公积金", "取公积金", "公积金提取", "销户提取"],
                "缴存": ["缴纳", "缴存公积金", "交公积金", "公积金缴存", "缴存金额"],
                "贷款": ["公积金贷款", "购房贷款", "房贷", "公积金房贷", "住房贷款"],
                "账户": ["公积金账户", "个人账户", "单位账户", "账户余额", "公积金账户状态"],
                "异地": ["外地", "非缴存地", "异地缴存", "跨省", "省内异地"],
                "转移": ["异地转移", "账户转移", "公积金转移", "转移接续", "转入转出"],
                "封存": ["账户封存", "封存公积金", "停缴封存", "公积金封存"],
                "启封": ["账户启封", "启封公积金", "恢复缴存"],
                "代际互助": ["亲属互助", "父母子女互助", "互助提取", "代际提取"],
                "还款": ["还贷", "偿还贷款", "公积金还款", "月供", "提前还款"]
            }

        def _build_synonym_dict(self) -> Dict:
            """构建公积金同义词字典"""
            return {
                "缴存人": ["公积金缴存者", "缴存职工", "个人缴存户", "单位缴存员工"],
                "灵活就业人员": ["自由职业者", "个体从业者", "自主就业人员", "个人缴存人员"],
                "缴存额": ["缴存金额", "缴纳数额", "缴存费用", "缴存款项"],
                "办理": ["申请", "申办", "经办", "手续办理", "业务办理"],
                "标准": ["规定", "政策", "基数标准", "比例标准", "缴存规范"],
                "权益": ["业务权益", "提取权益", "贷款权益", "公积金保障"],
                "登记": ["备案", "报备", "账户登记", "业务报备", "信息登记"],
                "封存": ["账户封存", "停缴封存", "封存登记", "缴存暂停"],
                "提取额": ["提取金额", "支取数额", "可提额度", "提取款项"],
                "贷款额": ["贷款金额", "可贷额度", "贷款数额", "放款金额"]
            }

        def _build_pattern_rules(self) -> List[Tuple[str, Dict]]:
            """构建公积金模式匹配规则"""
            return [
                # 公积金缴存业务相关模式
                (r'单位.*?公积金|职工.*?缴存|企业.*?缴存', {"first_level": "公积金缴存业务", "second_level": "缴存管理"}),
                (r'灵活就业.*?公积金|个人.*?缴存|自愿.*?缴存', {"first_level": "公积金缴存业务", "second_level": "缴存管理", "third_level": "缴存方式（单位/个人）"}),
                (r'增员.*?公积金|减员.*?公积金|人员.*?变更', {"first_level": "公积金缴存业务", "second_level": "缴存管理", "third_level": "缴存变更（增员/减员）"}),

                # 公积金提取业务相关模式
                (r'购房.*?提取|买房.*?公积金|购房.*?取', {"first_level": "公积金提取业务", "second_level": "提取类型", "third_level": "购房提取"}),
                (r'租房.*?提取|租房.*?公积金', {"first_level": "公积金提取业务", "second_level": "提取类型", "third_level": "租房提取"}),
                (r'离职.*?提取|辞职.*?公积金|外地户籍.*?离职', {"first_level": "公积金提取业务", "second_level": "提取类型", "third_level": "离职提取"}),
                (r'退休.*?提取|离休.*?公积金', {"first_level": "公积金提取业务", "second_level": "提取类型", "third_level": "退休提取"}),
                (r'代际.*?互助|父母.*?提取|子女.*?提取', {"first_level": "公积金提取业务", "second_level": "提取类型", "third_level": "代际互助提取"}),

                # 公积金贷款业务相关模式
                (r'公积金.*?贷款|购房.*?贷款|房贷.*?公积金', {"first_level": "公积金贷款业务", "second_level": "贷款申请"}),
                (r'提前.*?还款|提前.*?还贷|部分.*?还款', {"first_level": "公积金贷款业务", "second_level": "贷款管理", "third_level": "提前还款规定"}),
                (r'商转公.*?贷款|商业贷款.*?转', {"first_level": "公积金贷款业务", "second_level": "贷款办理指南", "third_level": "商转公贷款办理"}),

                # 公积金账户管理相关模式
                (r'公积金.*?账户|账户.*?余额|账户.*?封存', {"first_level": "公积金账户管理业务", "second_level": "账户维护"}),
                (r'异地.*?转移|外地.*?公积金|转移.*?接续', {"first_level": "公积金账户管理业务", "second_level": "账户维护", "third_level": "异地转移接续"}),
                (r'账户.*?变更|姓名.*?变更|身份证.*?修改', {"first_level": "公积金账户管理业务", "second_level": "账户维护", "third_level": "账户信息变更"}),

                # 业务办理相关模式
                (r'怎么.*?提取|如何.*?提取|提取.*?流程', {"action": "提取办理"}),
                (r'怎么.*?缴存|如何.*?缴存|缴存.*?方式', {"action": "缴存办理"}),
                (r'怎么.*?贷款|如何.*?贷款|贷款.*?流程', {"action": "贷款办理"}),

                # 专项业务相关模式
                (r'加装电梯.*?提取|电梯.*?公积金', {"first_level": "其他公积金政策", "second_level": "专项业务政策", "third_level": "老旧住宅加装电梯提取"}),
                (r'保障房.*?公积金|保障性住房.*?提取', {"first_level": "其他公积金政策", "second_level": "专项业务政策", "third_level": "保障性住房相关公积金政策"}),
            ]

        def _build_completeness_rules(self) -> Dict:
            """构建公积金信息完整性规则字典"""
            return {
                "购房提取": {
                    "required_slots": ["购房类型"],
                    "fallback_question": "请问您是本地购房还是异地购房？"
                },
                "租房提取": {
                    "required_slots": ["备案状态"],
                    "fallback_question": "请问您的租房是否已在住房租赁交易服务系统备案？"
                },
                "离职提取": {
                    "required_slots": ["户籍类型"],
                    "fallback_question": "请问您是本地户籍还是外地户籍？"
                },
                "代际互助提取": {
                    "required_slots": ["亲属关系"],
                    "fallback_question": "请问您与购房人是父母子女中的哪种亲属关系？"
                },
                "公积金贷款申请": {
                    "required_slots": ["缴存时长", "购房类型"],
                    "fallback_question": "请问您公积金缴存满多久了？是本地购房还是异地购房？"
                },
                "提前还款规定": {
                    "required_slots": ["贷款状态"],
                    "fallback_question": "请问您的公积金贷款目前是正常还款中还是处于其他状态？"
                },
                "商转公贷款办理": {
                    "required_slots": ["商业贷款状态"],
                    "fallback_question": "请问您的商业贷款目前是否正常还款？"
                },
                "异地转移接续": {
                    "required_slots": ["转移类型", "转移地区"],
                    "fallback_question": "请问您是要将公积金转入厦门还是转出厦门？具体涉及哪个地区？"
                },
                "缴存基数调整办理": {
                    "required_slots": ["缴存类型"],
                    "fallback_question": "请问您是单位缴存职工还是个人自愿缴存人员？"
                },
                "单位缴存登记": {
                    "required_slots": ["单位类型"],
                    "fallback_question": "请问您的单位是企业、机关事业单位还是其他类型？"
                },
                "账户信息变更": {
                    "required_slots": ["变更类型"],
                    "fallback_question": "请问您要变更的是姓名、身份证号还是银行卡等信息？"
                },
                "老旧住宅加装电梯提取": {
                    "required_slots": ["产权关系"],
                    "fallback_question": "请问您是房屋产权人还是产权人的子女？"
                },
                "灵活就业缴存申请": {
                    "required_slots": ["就业状态"],
                    "fallback_question": "请问您目前是否处于灵活就业状态？"
                }
            }

        def _extract_slots(self, query: str) -> Dict[str, bool]:
            """从查询中抽取公积金关键槽位是否存在"""
            query_lower = query.lower()
            return {
                "提取类型": any(kw in query_lower for kw in [
                    "购房", "租房", "离职", "退休", "离休", "代际互助", "出境", "大病", "残疾", 
                    "低保", "死亡", "加装电梯", "拆迁", "拍卖房", "自建房", "大修"
                ]),
                "贷款类型": any(kw in query_lower for kw in [
                    "公积金贷款", "商转公", "组合贷款", "异地贷款", "购房贷款", "房贷"
                ]),
                "缴存类型": any(kw in query_lower for kw in [
                    "单位缴存", "个人缴存", "灵活就业", "自愿缴存", "职工缴存"
                ]),
                "户籍类型": any(kw in query_lower for kw in [
                    "本地户籍", "外地户籍", "厦门户籍", "非厦门户籍", "户籍"
                ]),
                "购房类型": any(kw in query_lower for kw in [
                    "本地购房", "异地购房", "新建商品住房", "二手房", "拍卖房", "拆迁安置房", 
                    "保障性住房", "自建房", "预售房"
                ]),
                "备案状态": any(kw in query_lower for kw in [
                    "备案", "未备案", "住房租赁备案", "房屋备案"
                ]),
                "亲属关系": any(kw in query_lower for kw in [
                    "父母", "子女", "配偶", "亲属", "父子", "母子", "父女", "母女"
                ]),
                "转移类型": any(kw in query_lower for kw in [
                    "转入", "转出", "异地转移", "转移接续", "本地转入", "外地转出"
                ]),
                "转移地区": any(kw in query_lower for kw in [
                    "厦门", "省内", "省外", "福州", "泉州", "漳州", "北京", "上海", "广州", 
                    "深圳", "外地", "其他城市", "跨省", "跨市"
                ]),
                "缴存时长": any(kw in query_lower for kw in [
                    "缴存年限", "缴存年数", "累计缴存", "连续缴存", "缴存满", "缴存多少年"
                ]),
                "贷款状态": any(kw in query_lower for kw in [
                    "正常还款", "提前还款", "部分还款", "结清", "贷款展期", "还款中"
                ]),
                "变更类型": any(kw in query_lower for kw in [
                    "姓名", "身份证号", "银行卡", "联系方式", "单位信息", "缴存基数"
                ]),
                "产权关系": any(kw in query_lower for kw in [
                    "产权人", "产权人子女", "共有人", "房屋产权", "产权证明"
                ]),
                "就业状态": any(kw in query_lower for kw in [
                    "灵活就业", "在职", "离职", "失业", "就业", "退休"
                ]),
                "单位类型": any(kw in query_lower for kw in [
                    "企业", "机关事业单位", "个体户", "社会组织", "公司"
                ])
            }

        def _preprocess_query(self, query: str) -> str:
            """预处理查询文本"""
            # 转换为小写
            query = query.lower()
            # 移除多余空格
            query = re.sub(r'\s+', ' ', query).strip()
            # 替换同义词
            for main_word, synonyms in self.synonym_dict.items():
                for synonym in synonyms:
                    query = query.replace(synonym, main_word)
            return query

        def _calculate_keyword_similarity(self, query: str, keywords: List[str]) -> float:
            """计算关键词相似度"""
            query_words = set(jieba.lcut(query))
            keyword_matches = 0

            for keyword in keywords:
                keyword_words = set(jieba.lcut(keyword.lower()))
                if query_words & keyword_words:
                    keyword_matches += 1

            return keyword_matches / len(keywords) if keywords else 0

        def _pattern_match(self, query: str) -> Optional[Dict]:
            """模式匹配"""
            for pattern, result in self.pattern_rules:
                if re.search(pattern, query):
                    return result
            return None

        def _hierarchical_match(self, query: str) -> Tuple[float, Dict]:
            """层级匹配"""
            best_score = 0.0
            best_match = {}

            for first_level, second_level_data in self.intent_taxonomy.items():
                first_level_score = self._calculate_keyword_similarity(query, [first_level])

                if isinstance(second_level_data, dict):
                    # 有二级分类
                    for second_level, third_level_data in second_level_data.items():
                        second_level_score = self._calculate_keyword_similarity(query, [second_level])

                        if isinstance(third_level_data, dict):
                            # 有三级分类
                            for third_level, keywords in third_level_data.items():
                                third_level_score = self._calculate_keyword_similarity(query, keywords)
                                total_score = (first_level_score * 0.3 +
                                            second_level_score * 0.3 +
                                            third_level_score * 0.4)

                                if total_score > best_score:
                                    best_score = total_score
                                    best_match = {
                                        "first_level": first_level,
                                        "second_level": second_level,
                                        "third_level": third_level,
                                        "confidence": total_score,
                                        "action": f"{second_level}_{third_level}"
                                    }
                        else:
                            # 第三级是关键词列表
                            keywords = third_level_data
                            total_score = (first_level_score * 0.4 + second_level_score * 0.6)

                            if total_score > best_score:
                                best_score = total_score
                                best_match = {
                                    "first_level": first_level,
                                    "second_level": second_level,
                                    "third_level": "",
                                    "confidence": total_score,
                                    "action": second_level
                                }
                else:
                    # 第二级是关键词列表
                    keywords = second_level_data
                    total_score = first_level_score

                    if total_score > best_score:
                        best_score = total_score
                        best_match = {
                            "first_level": first_level,
                            "second_level": "",
                            "third_level": "",
                            "confidence": total_score,
                            "action": first_level
                        }

            return best_score, best_match

        def _rewrite_query(self, query: str, intent_result: Dict) -> str:
            """改写公积金查询"""
            rewritten = query

            # 添加公积金专业术语（基于一级分类）
            if intent_result.get("first_level"):
                first_level = intent_result["first_level"]
                if "缴存" not in rewritten and "公积金缴存业务" == first_level:
                    rewritten = f"公积金缴存业务：{rewritten}"
                elif "提取" not in rewritten and "公积金提取业务" == first_level:
                    rewritten = f"公积金提取业务：{rewritten}"
                elif "贷款" not in rewritten and "公积金贷款业务" == first_level:
                    rewritten = f"公积金贷款业务：{rewritten}"
                elif "账户" not in rewritten and "公积金账户管理业务" == first_level:
                    rewritten = f"公积金账户管理业务：{rewritten}"
                elif "政策" not in rewritten and "其他公积金政策" == first_level:
                    rewritten = f"其他公积金政策：{rewritten}"

            # 根据公积金业务类型添加关键词
            action = intent_result.get("action", "")
            if "提取办理" in action and "流程" not in rewritten:
                rewritten += " 提取流程"
            elif "缴存办理" in action and "标准" not in rewritten:
                rewritten += " 缴存标准"
            elif "贷款办理" in action and "流程" not in rewritten:
                rewritten += " 贷款流程"
            elif "转移办理" in action and "流程" not in rewritten:
                rewritten += " 转移流程"
            elif "账户变更" in action and "材料" not in rewritten:
                rewritten += " 变更材料"

            return rewritten.strip()

        def recognize_intent(self, query: str) -> IntentResult:
            """识别用户公积金业务意图"""
            # 预处理
            processed_query = self._preprocess_query(query)

            # 模式匹配
            pattern_result = self._pattern_match(processed_query)

            # 层级匹配
            hierarchical_score, hierarchical_result = self._hierarchical_match(processed_query)

            # 合并结果
            if pattern_result:
                final_result = {**hierarchical_result, **pattern_result}
            else:
                final_result = hierarchical_result

            # 设置默认值
            final_result.setdefault("first_level", "未分类")
            final_result.setdefault("second_level", "")
            final_result.setdefault("third_level", "")
            final_result.setdefault("confidence", 0.0)
            final_result.setdefault("action", "")

            # 改写查询
            rewritten_query = self._rewrite_query(query, final_result)

            # ===== 新增：完整性判断 =====
            needs_clarification = False
            clarification_question = ""

            # 获取当前三级意图（用于匹配公积金完整性规则）
            third_level_key = final_result.get("third_level") or final_result.get("second_level")
            completeness_rule = self.completeness_rules.get(third_level_key)

            if completeness_rule:
                slots = self._extract_slots(query)
                missing = [slot for slot in completeness_rule["required_slots"] if not slots.get(slot, False)]
                if missing:
                    needs_clarification = True
                    clarification_question = completeness_rule["fallback_question"]

            # 默认：低置信度也视为需澄清
            if not needs_clarification and final_result["confidence"] < 0.3:
                needs_clarification = True
                clarification_question = "您的问题不够明确，请具体说明您想了解的公积金事项（如缴存、提取、贷款、转移等）。"

            return IntentResult(
                first_level=final_result["first_level"],
                second_level=final_result["second_level"],
                third_level=final_result["third_level"],
                confidence=final_result["confidence"],
                action=final_result["action"],
                rewritten_query=rewritten_query,
                needs_clarification=needs_clarification,
                clarification_question=clarification_question
            )

# 初始化意图识别器
intent_recognizer = MedicalInsuranceIntentRecognizer()

@mcp.tool()
def recognize_user_intent(query: str) -> str:
    """
    识别用户意图并返回分类结果

    Args:
        query: 用户的原始查询文本

    Returns:
        JSON格式的意图识别结果，包含：
        - first_level: 一级分类
        - second_level: 二级分类
        - third_level: 三级分类
        - confidence: 置信度 (0-1)
        - action: 推荐的操作类型
        - rewritten_query: 改写后的查询
        - needs_clarification: 是否需要澄清信息
        - clarification_question: 反问内容（如果需要澄清）
    """
    try:
        result = intent_recognizer.recognize_intent(query)

        response = {
            "success": True,
            "data": {
                "first_level": result.first_level,
                "second_level": result.second_level,
                "third_level": result.third_level,
                "confidence": round(result.confidence, 3),
                "action": result.action,
                "rewritten_query": result.rewritten_query,
                "needs_clarification": result.needs_clarification,
                "clarification_question": result.clarification_question,
                "timestamp": datetime.now().isoformat()
            }
        }

        return json5.dumps(response, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"意图识别错误: {str(e)}")
        error_response = {
            "success": False,
            "error": f"意图识别失败: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
        return json5.dumps(error_response, ensure_ascii=False, indent=2)

@mcp.tool()
def rewrite_medical_query(query: str) -> str:
    """
    改写公积金相关问题，使其更专业和准确

    Args:
        query: 原始查询文本

    Returns:
        改写后的查询文本
    """
    try:
        # 先进行意图识别
        intent_result = intent_recognizer.recognize_intent(query)

        # 返回改写后的查询
        response = {
            "success": True,
            "data": {
                "original_query": query,
                "rewritten_query": intent_result.rewritten_query,
                "intent": {
                    "first_level": intent_result.first_level,
                    "second_level": intent_result.second_level,
                    "third_level": intent_result.third_level
                },
                "confidence": round(intent_result.confidence, 3),
                "needs_clarification": intent_result.needs_clarification,
                "clarification_question": intent_result.clarification_question,
                "timestamp": datetime.now().isoformat()
            }
        }

        return json5.dumps(response, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"查询改写错误: {str(e)}")
        error_response = {
            "success": False,
            "error": f"查询改写失败: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
        return json5.dumps(error_response, ensure_ascii=False, indent=2)

@mcp.tool()
def get_intent_taxonomy() -> str:
    """
    获取完整的意图分类体系

    Returns:
        完整的三级分类目录结构
    """
    try:
        response = {
            "success": True,
            "data": {
                "taxonomy": intent_recognizer.intent_taxonomy,
                "total_categories": len(intent_recognizer.intent_taxonomy),
                "timestamp": datetime.now().isoformat()
            }
        }

        return json5.dumps(response, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"获取分类体系错误: {str(e)}")
        error_response = {
            "success": False,
            "error": f"获取分类体系失败: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
        return json5.dumps(error_response, ensure_ascii=False, indent=2)

@mcp.tool()
def batch_intent_recognition(queries: list) -> str:
    """
    批量识别多个查询的意图

    Args:
        queries: 查询文本列表

    Returns:
        批量识别结果
    """
    try:
        results = []

        for query in queries:
            try:
                result = intent_recognizer.recognize_intent(query)
                results.append({
                    "query": query,
                    "success": True,
                    "first_level": result.first_level,
                    "second_level": result.second_level,
                    "third_level": result.third_level,
                    "confidence": round(result.confidence, 3),
                    "action": result.action,
                    "rewritten_query": result.rewritten_query,
                    "needs_clarification": result.needs_clarification,
                    "clarification_question": result.clarification_question
                })
            except Exception as e:
                results.append({
                    "query": query,
                    "success": False,
                    "error": str(e)
                })

        response = {
            "success": True,
            "data": {
                "results": results,
                "total_queries": len(queries),
                "successful_recognition": sum(1 for r in results if r["success"]),
                "timestamp": datetime.now().isoformat()
            }
        }

        return json5.dumps(response, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"批量意图识别错误: {str(e)}")
        error_response = {
            "success": False,
            "error": f"批量意图识别失败: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
        return json5.dumps(error_response, ensure_ascii=False, indent=2)

def main():
    """启动MCP服务器"""
    logger.info("启动意图识别MCP服务器...")
    mcp.run(transport='stdio')

if __name__ == '__main__':
    main()