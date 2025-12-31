"""
用户意图识别和问题改写MCP工具
用于医疗保险领域的智能意图分类和问题优化
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
    

class MedicalInsuranceIntentRecognizer:
    """医疗保险意图识别器"""

    def __init__(self):
        self.intent_taxonomy = self._build_intent_taxonomy()
        self.keyword_mappings = self._build_keyword_mappings()
        self.synonym_dict = self._build_synonym_dict()
        self.pattern_rules = self._build_pattern_rules()
        self.completeness_rules = self._build_completeness_rules()  # 新增：完整性规则

    def _build_intent_taxonomy(self) -> Dict:
        """构建意图分类体系"""
        return {
            "职工基本医疗保险": {
                "参保缴费": {
                    "参保对象": ["职工", "单位职工", "在职人员", "企业员工", "机关事业单位", "灵活就业"],
                    "缴费标准": ["缴费", "费用", "标准", "基数", "比例", "多少钱"],
                    "参保缴费方式": ["怎么交", "如何缴纳", "缴费方式", "代扣", "自缴"],
                    "参保缴费纠纷处理": ["纠纷", "争议", "投诉", "维权", "问题", "错误"],
                    "重复参保处理": ["重复参保", "多地参保", "双重参保", "冲突"],
                    "退费": ["退费", "退款", "返还", "多缴", "错缴"]
                },
                "医疗待遇": {
                    "待遇生效时间": ["生效时间", "开始时间", "等待期", "何时享受"],
                    "连续参保机制": ["连续参保", "断缴", "补缴", "连续性"],
                    "医保账户划拨": ["个人账户", "账户划拨", "返钱", "划入比例"],
                    "大病医保": ["大病", "重疾", "大病保险", "高额医疗"],
                    "医疗救助": ["医疗救助", "困难群众", "补助", "救助金"],
                    "待遇标准": ["报销比例", "封顶线", "起付线", "待遇标准"],
                    "就医使用": ["怎么用", "如何使用", "就医流程", "刷卡"]
                },
                "办事指南": {
                    "医疗费用报销办理": ["报销", "费用报销", "理赔", "怎么报销"],
                    "异地就医备案办理": ["异地就医", "外地就医", "备案", "转诊"],
                    "家庭共济办理": ["家庭共济", "家人使用", "配偶", "子女", "父母"],
                    "医保退休办理": ["医保退休", "退休医保", "缴费年限"],
                    "个人账户一次性支取办理": ["一次性支取", "账户提取", "清户", "销户"]
                },
                "转移接续手续办理": ["转移", "接续", "外地转入", "本地转出", "关系转移"]
            },
            "城乡居民医疗保险": {
                "参保缴费": {
                    "参保对象": ["居民", "城乡居民", "学生", "儿童", "老人", "无业人员"],
                    "缴费标准": ["缴费", "费用", "标准", "多少钱", "保费"],
                    "参保缴费方式": ["怎么交", "如何缴纳", "缴费方式", "线上缴费"],
                    "重复参保": ["重复参保", "双重参保", "冲突"],
                    "退费": ["退费", "退款", "返还", "多缴"]
                },
                "医疗待遇": {
                    "待遇生效时间": ["生效时间", "开始时间", "等待期"],
                    "参保长效机制": ["长效机制", "连续参保", "激励机制"],
                    "医保账户划拨": ["个人账户", "账户划拨", "门诊统筹"],
                    "大病医保": ["大病", "重疾", "大病保险"],
                    "医疗救助": ["医疗救助", "困难群众", "补助"],
                    "待遇标准": ["报销比例", "封顶线", "起付线"],
                    "就医使用": ["怎么用", "如何使用", "就医流程"]
                },
                "办事指南": {
                    "医疗费用报销办理": ["报销", "费用报销", "理赔"],
                    "异地就医备案办理": ["异地就医", "外地就医", "备案"],
                    "家庭共济办理": ["家庭共济", "家人使用"],
                    "转移接续手续办理": ["转移", "接续", "外地转入"]
                }
            },
            "生育保险": {
                "参保缴费": {
                    "参保对象": ["生育保险", "参保对象", "覆盖范围"],
                    "缴费标准": ["生育缴费", "费用标准", "缴费比例"],
                    "参保缴费方式": ["生育缴费方式", "怎么交"],
                    "参保缴费纠纷处理": ["生育纠纷", "争议处理"]
                },
                "生育待遇": {
                    "生育津贴待遇": ["生育津贴", "产假工资", "津贴标准"],
                    "男职工未就业配偶生育医疗费用待遇": ["配偶待遇", "男方配偶", "未就业配偶"],
                    "其他待遇": ["生育医疗", "产检", "分娩费用"]
                },
                "办事指南": {
                    "生育津贴办理": ["津贴办理", "生育津贴申请", "如何申请"],
                    "男职工未就业配偶生育医疗费用办理": ["配偶费用", "男方报销"]
                }
            },
            "其他医药政策": {
                "药品（含项目、耗材）政策": {
                    "药品目录": ["药品目录", "医保药品", "甲类乙类", "目录内药品"],
                    "医疗服务项目目录": ["服务项目", "诊疗项目", "医疗服务"],
                    "医用耗材目录": ["医用耗材", "器械", "植入材料"]
                },
                "DRG收费及按病种收费政策": {
                    "厦门市定点医疗机构就医": ["厦门DRG", "厦门病种收费", "厦门定点"],
                    "省内异地定点医疗机构就医": ["省内异地", "DRG异地"]
                },
                "辅助生殖政策": {
                    "福建省辅助生殖类医疗服务价格项目及省属公立医院项目价格表": ["辅助生殖", "试管婴儿", "人工授精", "价格表"],
                    "辅助生殖医保支付政策": ["辅助生殖医保", "试管医保", "支付政策"]
                },
                "补充医疗保险": {
                    "惠厦保": ["惠厦保", "补充保险", "商业保险"]
                },
                "长期护理险政策": ["长期护理", "护理保险", "失能护理"]
            }
        }

    def _build_keyword_mappings(self) -> Dict:
        """构建关键词映射"""
        return {
            # 同义词映射
            "医保": ["医疗保险", "医保", "社保医保", "基本医疗保险"],
            "报销": ["费用报销", "理赔", "结算", "费用返还"],
            "缴费": ["交费", "缴纳", "保费", "费用"],
            "账户": ["个人账户", "医保账户", "账户余额"],
            "异地": ["外地", "其他城市", "非参保地"],
            "生育": ["生孩子", "生育津贴", "产假"],
            "退休": ["养老", "退休人员", "退职"],
            "大病": ["重大疾病", "重疾", "大病保险"],
            "救助": ["补助", "救助金", "困难补助"]
        }

    def _build_synonym_dict(self) -> Dict:
        """构建同义词字典"""
        return {
            "职工": ["员工", "在职人员", "工作者"],
            "居民": ["城乡居民", "城镇居民", "农村居民"],
            "费用": ["钱", "金额", "收费", "价格"],
            "办理": ["申请", "手续", "流程"],
            "标准": ["规定", "政策", "制度"],
            "待遇": ["福利", "保障", "权益"],
            "备案": ["登记", "记录", "报备"]
        }

    def _build_pattern_rules(self) -> List[Tuple[str, Dict]]:
        """构建模式匹配规则"""
        return [
            # 职工医保相关模式
            (r'职工.*?医保|在职.*?医保|单位.*?医保', {"first_level": "职工基本医疗保险"}),
            (r'灵活就业.*?医保|个人.*?职工医保', {"first_level": "职工基本医疗保险"}),

            # 居民医保相关模式
            (r'居民.*?医保|城乡.*?医保|学生.*?医保', {"first_level": "城乡居民医疗保险"}),

            # 生育保险相关模式
            (r'生育.*?津贴|产假.*?工资|生孩子.*?补贴', {"first_level": "生育保险", "second_level": "生育待遇", "third_level": "生育津贴待遇"}),
            (r'男职工.*?配偶|未就业.*?配偶.*?生育', {"first_level": "生育保险", "second_level": "生育待遇", "third_level": "男职工未就业配偶生育医疗费用待遇"}),

            # 异地就医相关模式
            (r'异地.*?就医|外地.*?就医|跨省.*?就医', {"action": "异地就医备案"}),

            # 报销相关模式
            (r'怎么.*?报销|如何.*?报销|费用.*?报销', {"action": "医疗费用报销"}),

            # 缴费相关模式
            (r'怎么.*?缴费|如何.*?缴费|缴费.*?方式', {"action": "参保缴费"}),

            # 账户相关模式
            (r'个人.*?账户|账户.*?余额|账户.*?划拨', {"second_level": "医疗待遇", "third_level": "医保账户划拨"}),

            # 转移相关模式
            (r'关系.*?转移|转移.*?接续|外地.*?转入', {"second_level": "转移接续手续办理"}),

            # 家庭共济相关模式
            (r'家庭.*?共济|家人.*?使用|配偶.*?使用', {"second_level": "办事指南", "third_level": "家庭共济办理"}),

            # 大病相关模式
            (r'大病.*?保险|重疾.*?保险|高额.*?医疗', {"second_level": "医疗待遇", "third_level": "大病医保"}),
        ]

    def _build_completeness_rules(self) -> Dict:
        """构建信息完整性规则字典"""
        return {
            "医疗费用报销办理": {
                "required_slots": ["就医类型"],
                "fallback_question": "请问您需要报销的是门诊还是住院费用？"
            },
            "异地就医备案办理": {
                "required_slots": ["就医地"],
                "fallback_question": "请问您计划去哪个城市就医？"
            },
            "参保缴费方式": {
                "required_slots": ["参保类型"],
                "fallback_question": "请问您是职工、灵活就业人员，还是城乡居民？"
            },
            "缴费标准": {
                "required_slots": ["参保类型"],
                "fallback_question": "请问您想了解职工医保还是居民医保的缴费标准？"
            },
            "参保对象": {
                "required_slots": ["参保类型"],
                "fallback_question": "请问您想了解哪类人群的参保政策？"
            },
            "生育津贴待遇": {
                "required_slots": ["性别", "在职状态"],
                "fallback_question": "请问您是男职工还是女职工？目前是否在职？"
            },
            "男职工未就业配偶生育医疗费用待遇": {
                "required_slots": ["配偶状态"],
                "fallback_question": "请问您的配偶目前是否就业？"
            },
            "医保退休办理": {
                "required_slots": ["退休状态", "缴费年限"],
                "fallback_question": "请问您是否已退休？医保缴费满多少年了？"
            },
            "家庭共济办理": {
                "required_slots": ["家庭关系"],
                "fallback_question": "请问您想为哪位家人办理共济（配偶、子女还是父母）？"
            },
            "个人账户一次性支取办理": {
                "required_slots": ["支取原因"],
                "fallback_question": "请问您是因为什么情况需要一次性支取医保个人账户资金？"
            },
            "转移接续手续办理": {
                "required_slots": ["转移类型", "转移地区"],
                "fallback_question": "请问您需要从外地转入还是转出到外地？具体是哪个地区？"
            }
        }

    def _extract_slots(self, query: str) -> Dict[str, bool]:
        """从查询中抽取关键槽位是否存在"""
        query_lower = query.lower()
        return {
            "就医类型": any(kw in query_lower for kw in ["门诊", "住院", "急诊", "门急诊", "门特", "门诊特殊病"]),
            "就医地": any(kw in query_lower for kw in [
                "北京", "上海", "厦门", "外地", "城市", "某地", "哪个城市", "广州", "深圳", "杭州",
                "南京", "武汉", "成都", "重庆", "天津", "西安", "青岛", "大连", "宁波", "苏州"
            ]),
            "参保类型": any(kw in query_lower for kw in [
                "职工", "灵活就业", "居民", "学生", "老人", "城乡居民", "单位职工", "在职人员",
                "企业员工", "机关事业单位", "无业人员", "儿童", "学龄前儿童"
            ]),
            "性别": any(kw in query_lower for kw in ["男", "女", "男性", "女性", "先生", "女士"]),
            "在职状态": any(kw in query_lower for kw in ["在职", "退休", "离职", "工作", "失业", "就业"]),
            "配偶状态": any(kw in query_lower for kw in ["配偶", "爱人", "妻子", "丈夫", "老婆", "老公", "未就业", "失业"]),
            "退休状态": any(kw in query_lower for kw in ["退休", "退休人员", "养老", "退休年龄", "退休条件"]),
            "缴费年限": any(kw in query_lower for kw in ["缴费年限", "缴费年数", "累计缴费", "连续缴费", "缴费满", "缴费多少年"]),
            "家庭关系": any(kw in query_lower for kw in ["配偶", "子女", "父母", "家人", "父亲", "母亲", "儿子", "女儿", "孩子"]),
            "支取原因": any(kw in query_lower for kw in ["死亡", "出国", "移民", "转出", "销户", "清户", "继承", "遗属"]),
            "转移类型": any(kw in query_lower for kw in ["转入", "转出", "转移", "接续", "外地转入", "本地转出"]),
            "转移地区": any(kw in query_lower for kw in ["外地", "其他城市", "省外", "省内", "厦门", "北京", "上海", "广州", "深圳"])
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
        """改写查询"""
        rewritten = query

        # 添加专业术语
        if intent_result.get("first_level"):
            if "职工" not in rewritten and "职工基本医疗保险" == intent_result["first_level"]:
                rewritten = f"职工基本医疗保险：{rewritten}"
            elif "居民" not in rewritten and "城乡居民医疗保险" == intent_result["first_level"]:
                rewritten = f"城乡居民医疗保险：{rewritten}"

        # 根据意图类型添加关键词
        action = intent_result.get("action", "")
        if "报销" in action and "报销" not in rewritten:
            rewritten += " 报销流程"
        elif "缴费" in action and "缴费" not in rewritten:
            rewritten += " 缴费标准"
        elif "备案" in action and "备案" not in rewritten:
            rewritten += " 备案流程"

        return rewritten.strip()

    def recognize_intent(self, query: str) -> IntentResult:
        """识别用户意图"""
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

        # 获取当前三级意图（用于匹配规则）
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
            clarification_question = "您的问题不够明确，请具体说明您想了解的医保事项（如缴费、报销、异地就医等）。"

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
    改写医疗保险相关问题，使其更专业和准确

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