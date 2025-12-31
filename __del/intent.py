"""
医疗保险智能意图识别与检索整合系统
整合意图识别、多级检索和智能融合的核心组件
"""

import copy
import json
import re
import jieba
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
import logging
from functools import wraps
import hashlib

from qwen_agent.llm.schema import ContentItem, Message, ROLE, CONTENT
from app.core.vector import (
    doc_hybrid_search_bm25_vec,
    qa_hybrid_search_bm25_vec,
    get_text_embeddings
)
from app.config.llm_client import embedding_client
from app.config.database import SessionLocal
from sqlalchemy import text

logger = logging.getLogger(__name__)


# ==================== 数据结构定义 ====================

@dataclass
class IntentResult:
    """意图识别结果"""
    first_level: str
    second_level: str
    third_level: str
    confidence: float
    action: str
    rewritten_query: str
    needs_clarification: bool
    clarification_question: str
    keywords: List[str] = None  # 新增：提取的关键词

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


@dataclass
class SearchResult:
    """搜索结果"""
    id: str
    question: str
    answer: str
    final_score: float
    bm25_score: float = 0.0
    vec_score: float = 0.0
    match_sources: List[str] = None
    intent_relevance: float = 0.0

    def __post_init__(self):
        if self.match_sources is None:
            self.match_sources = []


@dataclass
class ConversationContext:
    """对话上下文"""
    user_id: str
    session_id: str
    history: List[Message] = None
    intent_history: List[IntentResult] = None
    current_intent: Optional[IntentResult] = None
    slots_filled: Dict[str, Any] = None

    def __post_init__(self):
        if self.history is None:
            self.history = []
        if self.intent_history is None:
            self.intent_history = []
        if self.slots_filled is None:
            self.slots_filled = {}


# ==================== 缓存装饰器 ====================

def simple_cache(timeout_seconds: int = 300):
    """简单内存缓存装饰器"""
    cache = {}

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = hashlib.md5(
                f"{func.__name__}_{str(args)}_{str(sorted(kwargs.items()))}".encode()
            ).hexdigest()

            # 检查缓存
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                import time
                if time.time() - timestamp < timeout_seconds:
                    return result

            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            import time
            cache[cache_key] = (result, time.time())

            return result
        return wrapper
    return decorator


# ==================== 意图识别核心类 ====================

class MedicalInsuranceIntentRecognizer:
    """医疗保险意图识别器（简化版核心逻辑）"""

    def __init__(self):
        self.intent_taxonomy = self._build_intent_taxonomy()
        self.keyword_mappings = self._build_keyword_mappings()
        self.synonym_dict = self._build_synonym_dict()
        self.pattern_rules = self._build_pattern_rules()
        self.completeness_rules = self._build_completeness_rules()

    def _build_intent_taxonomy(self) -> Dict:
        """构建意图分类体系"""
        return {
            "职工基本医疗保险": {
                "参保缴费": {
                    "参保对象": ["职工", "单位职工", "在职人员", "企业员工", "机关事业单位", "灵活就业"],
                    "缴费标准": ["缴费", "费用", "标准", "基数", "比例", "多少钱"],
                    "参保缴费方式": ["怎么交", "如何缴纳", "缴费方式", "代扣", "自缴"],
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
                },
                "办事指南": {
                    "医疗费用报销办理": ["报销", "费用报销", "理赔", "怎么报销"],
                    "异地就医备案办理": ["异地就医", "外地就医", "备案", "转诊"],
                    "家庭共济办理": ["家庭共济", "家人使用", "配偶", "子女", "父母"],
                    "医保退休办理": ["医保退休", "退休医保", "缴费年限"],
                    "个人账户一次性支取办理": ["一次性支取", "账户提取", "清户", "销户"]
                }
            },
            "城乡居民医疗保险": {
                "参保缴费": {
                    "参保对象": ["居民", "城乡居民", "学生", "儿童", "老人", "无业人员"],
                    "缴费标准": ["缴费", "费用", "标准", "多少钱", "保费"],
                    "参保缴费方式": ["怎么交", "如何缴纳", "缴费方式", "线上缴费"],
                },
                "医疗待遇": {
                    "待遇生效时间": ["生效时间", "开始时间", "等待期"],
                    "参保长效机制": ["长效机制", "连续参保", "激励机制"],
                    "医保账户划拨": ["个人账户", "账户划拨", "门诊统筹"],
                    "大病医保": ["大病", "重疾", "大病保险"],
                    "医疗救助": ["医疗救助", "困难群众", "补助"],
                    "待遇标准": ["报销比例", "封顶线", "起付线"],
                },
                "办事指南": {
                    "医疗费用报销办理": ["报销", "费用报销", "理赔"],
                    "异地就医备案办理": ["异地就医", "外地就医", "备案"],
                    "家庭共济办理": ["家庭共济", "家人使用"],
                }
            },
            "生育保险": {
                "参保缴费": {
                    "参保对象": ["生育保险", "参保对象", "覆盖范围"],
                    "缴费标准": ["生育缴费", "费用标准", "缴费比例"],
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
                "补充医疗保险": {
                    "惠厦保": ["惠厦保", "补充保险", "商业保险"]
                },
                "长期护理险政策": ["长期护理", "护理保险", "失能护理"]
            }
        }

    def _build_keyword_mappings(self) -> Dict:
        """构建关键词映射"""
        return {
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
            (r'职工.*?医保|在职.*?医保|单位.*?医保', {"first_level": "职工基本医疗保险"}),
            (r'灵活就业.*?医保|个人.*?职工医保', {"first_level": "职工基本医疗保险"}),
            (r'居民.*?医保|城乡.*?医保|学生.*?医保', {"first_level": "城乡居民医疗保险"}),
            (r'生育.*?津贴|产假.*?工资|生孩子.*?补贴', {"first_level": "生育保险", "second_level": "生育待遇", "third_level": "生育津贴待遇"}),
            (r'异地.*?就医|外地.*?就医|跨省.*?就医', {"action": "异地就医备案"}),
            (r'怎么.*?报销|如何.*?报销|费用.*?报销', {"action": "医疗费用报销"}),
            (r'怎么.*?缴费|如何.*?缴费|缴费.*?方式', {"action": "参保缴费"}),
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
            "生育津贴待遇": {
                "required_slots": ["性别", "在职状态"],
                "fallback_question": "请问您是男职工还是女职工？目前是否在职？"
            },
            "家庭共济办理": {
                "required_slots": ["家庭关系"],
                "fallback_question": "请问您想为哪位家人办理共济（配偶、子女还是父母）？"
            },
        }

    def _extract_keywords(self, query: str) -> List[str]:
        """提取查询关键词"""
        # 使用jieba分词并过滤停用词
        words = jieba.lcut(query)
        stop_words = {'的', '了', '在', '是', '我', '你', '他', '她', '它', '们', '这', '那', '有', '和', '与', '或'}
        keywords = [word for word in words if len(word) > 1 and word not in stop_words]

        # 添加意图特定关键词
        query_lower = query.lower()
        for main_word, synonyms in self.keyword_mappings.items():
            if any(synonym in query_lower for synonym in synonyms):
                keywords.append(main_word)

        return list(set(keywords))

    def _extract_slots(self, query: str) -> Dict[str, bool]:
        """从查询中抽取关键槽位是否存在"""
        query_lower = query.lower()
        return {
            "就医类型": any(kw in query_lower for kw in ["门诊", "住院", "急诊", "门急诊"]),
            "就医地": any(kw in query_lower for kw in ["北京", "上海", "厦门", "外地", "城市", "广州", "深圳"]),
            "参保类型": any(kw in query_lower for kw in ["职工", "灵活就业", "居民", "学生", "老人", "城乡居民"]),
            "性别": any(kw in query_lower for kw in ["男", "女", "男性", "女性", "先生", "女士"]),
            "在职状态": any(kw in query_lower for kw in ["在职", "退休", "离职", "工作", "失业", "就业"]),
            "家庭关系": any(kw in query_lower for kw in ["配偶", "子女", "父母", "家人", "父亲", "母亲"]),
        }

    def _hierarchical_match(self, query: str) -> Tuple[float, Dict]:
        """层级匹配"""
        best_score = 0.0
        best_match = {}
        query_words = set(jieba.lcut(query.lower()))

        for first_level, second_level_data in self.intent_taxonomy.items():
            first_level_score = len(query_words & set(jieba.lcut(first_level))) / len(set(jieba.lcut(first_level))) if first_level else 0

            if isinstance(second_level_data, dict):
                for second_level, third_level_data in second_level_data.items():
                    second_level_score = len(query_words & set(jieba.lcut(second_level))) / len(set(jieba.lcut(second_level))) if second_level else 0

                    if isinstance(third_level_data, dict):
                        for third_level, keywords in third_level_data.items():
                            third_level_score = len(query_words & set(jieba.lcut(' '.join(keywords)))) / len(set(jieba.lcut(' '.join(keywords)))) if keywords else 0
                            total_score = (first_level_score * 0.3 + second_level_score * 0.3 + third_level_score * 0.4)

                            if total_score > best_score:
                                best_score = total_score
                                best_match = {
                                    "first_level": first_level,
                                    "second_level": second_level,
                                    "third_level": third_level,
                                    "confidence": total_score,
                                    "action": f"{second_level}_{third_level}"
                                }

        return best_score, best_match

    def recognize_intent(self, query: str) -> IntentResult:
        """识别用户意图"""
        # 预处理
        query = query.lower().strip()

        # 层级匹配
        hierarchical_score, hierarchical_result = self._hierarchical_match(query)

        # 设置默认值
        final_result = hierarchical_result
        final_result.setdefault("first_level", "未分类")
        final_result.setdefault("second_level", "")
        final_result.setdefault("third_level", "")
        final_result.setdefault("confidence", 0.0)
        final_result.setdefault("action", "")

        # 提取关键词
        keywords = self._extract_keywords(query)

        # 完整性判断
        needs_clarification = False
        clarification_question = ""

        third_level_key = final_result.get("third_level") or final_result.get("second_level")
        completeness_rule = self.completeness_rules.get(third_level_key)

        if completeness_rule:
            slots = self._extract_slots(query)
            missing = [slot for slot in completeness_rule["required_slots"] if not slots.get(slot, False)]
            if missing:
                needs_clarification = True
                clarification_question = completeness_rule["fallback_question"]

        # 低置信度也视为需澄清
        if not needs_clarification and final_result["confidence"] < 0.3:
            needs_clarification = True
            clarification_question = "您的问题不够明确，请具体说明您想了解的医保事项（如缴费、报销、异地就医等）。"

        return IntentResult(
            first_level=final_result["first_level"],
            second_level=final_result["second_level"],
            third_level=final_result["third_level"],
            confidence=final_result["confidence"],
            action=final_result["action"],
            rewritten_query=query,  # 简化版直接返回原查询
            needs_clarification=needs_clarification,
            clarification_question=clarification_question,
            keywords=keywords
        )


# ==================== 检索策略管理器 ====================

class SearchStrategyManager:
    """搜索策略管理器"""

    # 意图分类与检索策略映射
    INTENT_SEARCH_STRATEGY = {
        "办事指南": {
            "bm25_weight": 0.7,
            "vector_weight": 0.3,
            "similarity_threshold": 0.85,
            "boost_keywords": True,
            "top_k": 5
        },
        "医疗待遇": {
            "bm25_weight": 0.4,
            "vector_weight": 0.6,
            "similarity_threshold": 0.75,
            "boost_keywords": False,
            "top_k": 5
        },
        "参保缴费": {
            "bm25_weight": 0.5,
            "vector_weight": 0.5,
            "similarity_threshold": 0.80,
            "boost_keywords": True,
            "top_k": 5
        },
        "default": {
            "bm25_weight": 0.5,
            "vector_weight": 0.5,
            "similarity_threshold": 0.75,
            "boost_keywords": False,
            "top_k": 5
        }
    }

    @classmethod
    def get_strategy(cls, intent_result: IntentResult) -> Dict:
        """根据意图结果获取检索策略"""
        return cls.INTENT_SEARCH_STRATEGY.get(
            intent_result.second_level,
            cls.INTENT_SEARCH_STRATEGY["default"]
        )


# ==================== 意图感知的搜索引擎 ====================

class IntentAwareSearchEngine:
    """意图感知的搜索引擎"""

    def __init__(self):
        self.intent_recognizer = MedicalInsuranceIntentRecognizer()

    @simple_cache(timeout_seconds=300)
    def recognize_intent(self, query: str) -> IntentResult:
        """识别用户意图（带缓存）"""
        return self.intent_recognizer.recognize_intent(query)

    def optimize_query_by_intent(self, query: str, intent_result: IntentResult) -> str:
        """基于意图优化查询"""
        optimized_query = query

        # 添加意图关键词
        if intent_result.keywords:
            optimized_query += " " + " ".join(intent_result.keywords)

        # 根据意图类型添加专业术语
        if intent_result.first_level == "职工基本医疗保险" and "职工" not in optimized_query:
            optimized_query = f"职工医保 {optimized_query}"
        elif intent_result.first_level == "城乡居民医疗保险" and "居民" not in optimized_query:
            optimized_query = f"居民医保 {optimized_query}"

        return optimized_query.strip()

    def multi_recall_search(self, query: str, intent_result: IntentResult) -> Dict[str, List[Dict]]:
        """多路召回搜索"""
        strategy = SearchStrategyManager.get_strategy(intent_result)

        # 优化查询
        optimized_query = self.optimize_query_by_intent(query, intent_result)

        # 并行执行多种搜索
        with ThreadPoolExecutor(max_workers=2) as executor:
            # QA知识库搜索
            qa_future = executor.submit(
                qa_hybrid_search_bm25_vec,
                optimized_query
            )

            # 文档知识库搜索
            doc_future = executor.submit(
                doc_hybrid_search_bm25_vec,
                optimized_query
            )

        qa_results = qa_future.result()
        doc_results = doc_future.result()

        return {
            "qa": qa_results,
            "doc": doc_results,
            "strategy": strategy
        }

    def calculate_intent_relevance_bonus(self, doc: Dict, intent_result: IntentResult) -> float:
        """计算意图相关性加分"""
        bonus = 0.0
        doc_content = f"{doc.get('question', '')} {doc.get('answer', '')}".lower()

        # 意图关键词匹配加分
        for keyword in intent_result.keywords:
            if keyword.lower() in doc_content:
                bonus += 0.05

        # 一级分类匹配加分
        if intent_result.first_level.lower() in doc_content:
            bonus += 0.1

        # 二级分类匹配加分
        if intent_result.second_level.lower() in doc_content:
            bonus += 0.08

        return min(bonus, 0.3)  # 最高0.3分加分

    def fuse_results_with_rrf(self, search_results: Dict, intent_result: IntentResult) -> List[SearchResult]:
        """使用RRF融合搜索结果"""
        strategy = search_results["strategy"]
        k = 60  # RRF参数

        doc_scores = {}
        doc_data = {}

        # 合并QA和文档结果
        all_results = []
        all_results.extend(search_results.get("qa", []))
        all_results.extend(search_results.get("doc", []))

        # 去重（基于ID）
        unique_docs = {}
        for doc in all_results:
            doc_id = doc["id"]
            if doc_id not in unique_docs:
                unique_docs[doc_id] = doc
            else:
                # 合并分数
                existing_doc = unique_docs[doc_id]
                if "bm25_score" in doc:
                    existing_doc["bm25_score"] = max(existing_doc.get("bm25_score", 0), doc["bm25_score"])
                if "vec_score" in doc:
                    existing_doc["vec_score"] = max(existing_doc.get("vec_score", 0), doc["vec_score"])

        # RRF评分
        for rank, doc in enumerate(unique_docs.values(), 1):
            doc_id = doc["id"]
            bm25_score = doc.get("bm25_score", 0)
            vec_score = doc.get("vec_score", 0)

            # 标准化分数
            normalized_bm25 = min(bm25_score / 100.0, 1.0) if bm25_score > 0 else 0
            normalized_vec = min(vec_score, 1.0) if vec_score > 0 else 0

            # 加权平均
            hybrid_score = (strategy["bm25_weight"] * normalized_bm25 +
                          strategy["vector_weight"] * normalized_vec)

            # 意图相关性加分
            intent_bonus = self.calculate_intent_relevance_bonus(doc, intent_result)
            final_score = hybrid_score + intent_bonus

            doc_scores[doc_id] = final_score
            doc_data[doc_id] = doc

        # 按最终得分排序
        final_results = []
        for doc_id, score in sorted(doc_scores.items(), key=lambda x: x[1], reverse=True):
            doc = doc_data[doc_id]
            result = SearchResult(
                id=str(doc["id"]),
                question=doc.get("question", ""),
                answer=doc.get("answer", ""),
                final_score=score,
                bm25_score=doc.get("bm25_score", 0.0),
                vec_score=doc.get("vec_score", 0.0),
                intent_relevance=score - (doc.get("bm25_score", 0) + doc.get("vec_score", 0))
            )
            final_results.append(result)

        return final_results[:strategy["top_k"]]

    def search(self, query: str) -> Tuple[IntentResult, List[SearchResult]]:
        """执行完整的意图识别+搜索流程"""
        # 1. 意图识别
        intent_result = self.recognize_intent(query)

        # 2. 如果需要澄清，直接返回
        if intent_result.needs_clarification:
            return intent_result, []

        # 3. 多路召回搜索
        search_results = self.multi_recall_search(query, intent_result)

        # 4. 结果融合
        fused_results = self.fuse_results_with_rrf(search_results, intent_result)

        return intent_result, fused_results


# ==================== 对话管理器 ====================

class ConversationManager:
    """对话管理器"""

    def __init__(self):
        self.search_engine = IntentAwareSearchEngine()
        self.contexts: Dict[str, ConversationContext] = {}

    def get_or_create_context(self, user_id: str, session_id: str) -> ConversationContext:
        """获取或创建对话上下文"""
        context_key = f"{user_id}:{session_id}"
        if context_key not in self.contexts:
            self.contexts[context_key] = ConversationContext(
                user_id=user_id,
                session_id=session_id
            )
        return self.contexts[context_key]

    def process_message(self, user_id: str, session_id: str, message: str) -> Tuple[IntentResult, List[SearchResult], str]:
        """处理用户消息"""
        # 获取对话上下文
        context = self.get_or_create_context(user_id, session_id)

        # 意图识别和搜索
        intent_result, search_results = self.search_engine.search(message)

        # 更新上下文
        context.current_intent = intent_result
        context.intent_history.append(intent_result)

        # 生成响应文本
        response_text = self.generate_response(intent_result, search_results, context)

        return intent_result, search_results, response_text

    def generate_response(self, intent_result: IntentResult, search_results: List[SearchResult], context: ConversationContext) -> str:
        """生成响应文本"""
        # 如果需要澄清
        if intent_result.needs_clarification:
            return intent_result.clarification_question

        # 如果没有搜索结果
        if not search_results:
            return "抱歉，我没有找到相关的医保信息，请您换一种方式提问。"

        # 生成基于搜索结果的响应
        best_result = search_results[0]
        response = f"根据您关于{intent_result.second_level}的问题，我为您找到以下信息：\n\n"
        response += f"{best_result.answer}\n\n"

        # 如果置信度较低，建议进一步明确
        if intent_result.confidence < 0.6:
            response += "如果您需要更具体的信息，建议您详细说明您的情况。"

        return response


# ==================== 工具函数 ====================

def format_knowledge_to_source_and_content(search_results: List[SearchResult]) -> List[Dict]:
    """将搜索结果转换为知识格式"""
    knowledge = []
    for result in search_results:
        knowledge.append({
            'source': f'知识库文档#{result.id}',
            'content': result.answer
        })
    return knowledge


def create_knowledge_prompt(search_results: List[SearchResult], lang: str = 'zh') -> str:
    """创建知识提示"""
    if not search_results:
        return ""

    knowledge_snippets = []
    for result in search_results:
        snippet = f"## 来自 {result.source if hasattr(result, 'source') else '知识库'} 的内容：\n\n```\n{result.answer}\n```"
        knowledge_snippets.append(snippet)

    knowledge_prompt = f"# 知识库\n\n{chr(10).join(knowledge_snippets)}"
    return knowledge_prompt


# ==================== 全局实例 ====================

# 创建全局实例
intent_search_engine = IntentAwareSearchEngine()
conversation_manager = ConversationManager()


# ==================== 使用示例 ====================

"""
使用示例：

# 1. 基本的意图识别+搜索
from app.core.intent import intent_search_engine

query = "我想了解医保报销流程"
intent_result, search_results = intent_search_engine.search(query)

print(f"识别意图: {intent_result.first_level} -> {intent_result.second_level}")
print(f"置信度: {intent_result.confidence}")
print(f"搜索结果数量: {len(search_results)}")

for i, result in enumerate(search_results, 1):
    print(f"{i}. {result.question}")
    print(f"   评分: {result.final_score:.4f}")
    print(f"   回答: {result.answer[:100]}...")


# 2. 对话式交互
from app.core.intent import conversation_manager

# 处理用户消息
user_id = "user123"
session_id = "session456"
message = "职工医保怎么报销？"

intent_result, search_results, response = conversation_manager.process_message(
    user_id, session_id, message
)

print(f"助手回复: {response}")


# 3. 仅意图识别
from app.core.intent import MedicalInsuranceIntentRecognizer

recognizer = MedicalInsuranceIntentRecognizer()
intent_result = recognizer.recognize_intent("我想了解生育津贴")

if intent_result.needs_clarification:
    print(f"需要澄清: {intent_result.clarification_question}")
else:
    print(f"识别结果: {intent_result.second_level} - {intent_result.third_level}")


# 4. 与Assistant类集成示例
class EnhancedAssistant(Assistant):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.conversation_manager = conversation_manager

    def _run_with_intent(self, messages: List[Message], **kwargs):
        \"\"\"集成意图识别的运行方法\"\"\"
        # 获取用户查询
        query = ""
        for msg in reversed(messages):
            if msg.get(ROLE) == 'user':
                content = msg.get(CONTENT, '')
                if isinstance(content, str):
                    query = content.strip()
                elif isinstance(content, list):
                    query = " ".join([item.text if hasattr(item, 'text') else str(item) for item in content])
                break

        if not query:
            return super()._run(messages, **kwargs)

        # 使用意图识别处理
        try:
            intent_result, search_results, response = self.conversation_manager.process_message(
                "anonymous", "default", query
            )

            # 如果需要澄清，返回澄清问题
            if intent_result.needs_clarification:
                clarification_msg = Message(
                    role=ROLE,
                    content=ContentItem(text=intent_result.clarification_question)
                )
                yield [clarification_msg]
                return

            # 如果有搜索结果，将结果作为知识传递给原有逻辑
            if search_results:
                # 将搜索结果转换为知识格式
                knowledge = format_knowledge_to_source_and_content(search_results)
                knowledge_json = json.dumps([{
                    'url': f'doc_{result.id}',
                    'text': [result.answer]
                } for result in search_results], ensure_ascii=False)

                # 调用原有的知识检索逻辑
                return super()._run(messages=messages, knowledge=knowledge_json, **kwargs)

        except Exception as e:
            logger.error(f"意图识别处理失败: {e}")

        # 回退到原有逻辑
        return super()._run(messages=messages, **kwargs)


# 5. 性能监控和优化
import time

def benchmark_search_performance(test_queries: List[str]):
    \"\"\"搜索性能基准测试\"\"\"
    total_time = 0
    successful_searches = 0

    for query in test_queries:
        start_time = time.time()

        try:
            intent_result, search_results = intent_search_engine.search(query)
            end_time = time.time()

            total_time += (end_time - start_time)
            successful_searches += 1

            print(f"查询: {query}")
            print(f"  意图: {intent_result.second_level} (置信度: {intent_result.confidence:.3f})")
            print(f"  结果: {len(search_results)} 条")
            print(f"  耗时: {end_time - start_time:.3f}s")
            print()

        except Exception as e:
            print(f"查询失败: {query} - {e}")

    if successful_searches > 0:
        avg_time = total_time / successful_searches
        print(f"平均响应时间: {avg_time:.3f}s")
        print(f"成功率: {successful_searches}/{len(test_queries)} ({successful_searches/len(test_queries)*100:.1f}%)")


# 使用基准测试
if __name__ == "__main__":
    test_queries = [
        "职工医保怎么报销？",
        "生育津贴怎么申请？",
        "异地就医备案流程",
        "医保个人账户余额查询",
        "灵活就业人员医保缴费标准"
    ]

    benchmark_search_performance(test_queries)
"""