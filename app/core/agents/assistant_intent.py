"""
意图识别bot
"""
import logging
from typing import List, Dict
from app.config.llm_client import embedding_client, chat_client_bot

from app.core.rag.rag_search import RAGSearch

class IntentAgent:
    """基于RAG的意图分类器"""

    def __init__(self):
        self.client = chat_client_bot

        # 预定义的类别体系
        self.intent_categories = {
            "职工基本医疗保险": {
                "参保缴费": ["参保对象", "缴费标准", "参保缴费方式", "参保缴费纠纷处理", "重复参保处理", "退费"],
                "医疗待遇": ["待遇生效时间", "连续参保机制", "医保账户划拨", "大病医保", "医疗救助", "待遇标准", "就医使用"],
                "办事指南": ["转移接续手续办理", "医疗费用报销办理", "异地就医备案办理", "家庭共济办理", "医保退休办理", "个人账户一次性支取办理"]
            },
            "城乡居民医疗保险": {
                "参保缴费": ["参保对象", "缴费标准", "参保缴费方式", "重复参保", "退费"],
                "医疗待遇": ["待遇生效时间", "参保长效机制", "医保账户划拨", "大病医保", "医疗救助", "待遇标准", "就医使用"],
                "办事指南": ["医疗费用报销办理", "异地就医备案办理", "家庭共济办理", "转移接续手续办理"]
            },
            "生育保险": {
                "参保缴费": ["参保对象", "缴费标准", "参保缴费方式", "参保缴费纠纷处理"],
                "生育待遇": ["生育津贴待遇", "男职工未就业配偶生育医疗费用待遇", "其他待遇"],
                "办事指南": ["生育津贴办理", "男职工未就业配偶生育医疗费用办理"]
            },
            "其他医药政策": {
                "药品（含项目、耗材）政策": ["药品目录", "医疗服务项目目录", "医用耗材目录"],
                "DRG收费及按病种收费政策": ["厦门市定点医疗机构就医", "省内异地定点医疗机构就医"],
                "辅助生殖政策": ["福建省辅助生殖类医疗服务价格项目及省属公立医院项目价格表", "辅助生殖医保支付政策"],
                "补充医疗保险": ["惠厦保"],
                "长期护理险政策": ["未分类"]
            }
        }

    def _build_classification_prompt(self, 
                                     query: str, 
                                     search_results: List[Dict],
                                     graph_knowledge: str) -> str:
        """
        构建意图分类的提示词

        Args:
            query: 用户查询
            search_results: RAG搜索结果
            graph_knowledge: 图谱知识提示词

        Returns:
            构建好的提示词
        """
        # 格式化搜索结果
        context = ""
        if search_results:
            context = "\n\n相关参考信息：\n"
            for i, result in enumerate(search_results[:5], 1):
                context += f"{i}. 问题：{result.get('question', '')}\n"
                context += f"   答案：{result.get('answer', '')[:200]}...\n\n"

        # 格式化类别体系
        category_str = ""
        for main_cat, sub_cats in self.intent_categories.items():
            category_str += f"\n{main_cat}：\n"
            for sub_cat, details in sub_cats.items():
                category_str += f"  - {sub_cat}：{', '.join(details)}\n"

        prompt = f"""你是一个专业的医保政策意图分类专家。请根据用户查询和相关参考信息，准确识别用户意图所属的类别。

用户查询：{query}
{graph_knowledge}

{context}

可选类别体系：{category_str}

请按照以下要求进行分类：
1. 分析用户查询的主要意图和关键词
2. 参考相关信息的上下文内容
3. 选择最匹配的一级分类、二级分类和三级分类
4. 如果你判断无法匹配，请返回未分类
5. 返回JSON格式的分类结果

返回格式示例：
{{
    "main_category": "职工基本医疗保险",
    "sub_category": "参保缴费",
    "detail_category": "参保对象",
    "confidence": 0.95,
    "reason": "用户询问的是职工基本医疗保险的参保对象问题，关键词匹配度高"
}}

请直接返回JSON结果，不要包含其他说明文字。"""

        return prompt

    def classify_intent(self, query: str, top_k: int = 5) -> Dict:
        """
        使用RAG+LLM进行意图分类

        Args:
            query: 用户查询文本
            top_k: 搜索结果数量

        Returns:
            分类结果字典
        """
        try:
            # 1. 使用知识图谱搜索相关参考信息
            
            search_service = RAGSearch()
            graph_result = search_service._knowledge_graph_search(query=query)


            

            # 2. 构建分类提示词
            prompt = self._build_classification_prompt(query, graph_knowledge=graph_result)

            # 3. 调用LLM进行分类
            response = self.client.chat.completions.create(
                model="glm-4.5-air",
                messages=[
                    {"role": "system", "content": "你是一个专业的医保政策意图分类专家，负责准确识别用户查询的意图类别。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500,
                extra_body={
                    'enable_thinking': False,
                    "thinking": {
                        "type": "disabled",
                    }
                }
            )

            # 4. 解析LLM响应
            result_text = response.choices[0].message.content.strip() if response.choices[0].message.content else ""
            
            # 尝试解析JSON
            import json
            try:
                result = json.loads(result_text)
                # 添加搜索结果信息
                result["search_results_count"] = len(search_results)
                result["search_context"] = search_results[:2] if search_results else []
                # 使用搜索结果的最低相似度作为置信度基础
                if search_results:
                    min_similarity = min(
                        (search_result.get('vec_score', 0) or search_result.get('bm25_score', 0) or search_result.get('rerank_score', 0) or 0)
                        for search_result in search_results
                    )
                    result["confidence"] = min(result.get("confidence", 0.5), min_similarity)
                else:
                    result["confidence"] = result.get("confidence", 0.3)
                return result
            except json.JSONDecodeError:
                # 如果JSON解析失败，返回默认结构
                return {
                    "main_category": "未识别",
                    "sub_category": "未识别",
                    "detail_category": "未识别",
                    "confidence": 0.0,
                    "reason": "LLM响应解析失败",
                    "raw_response": result_text,
                    "search_results_count": len(search_results),
                    "search_context": search_results[:2] if search_results else []
                }

        except Exception as e:
            logging.error(f"意图分类失败: {e}")
            return {
                "main_category": "错误",
                "sub_category": "错误",
                "detail_category": "错误",
                "confidence": 0.0,
                "reason": f"分类过程出现异常: {str(e)}",
                "search_results_count": 0,
                "search_context": []
            }

    def batch_classify(self, queries: List[str]) -> List[Dict]:
        """
        批量意图分类

        Args:
            queries: 查询文本列表

        Returns:
            分类结果列表
        """
        results = []
        for query in queries:
            result = self.classify_intent(query)
            results.append(result)
        return results

    def get_category_stats(self, classified_results: List[Dict]) -> Dict:
        """
        统计分类结果分布

        Args:
            classified_results: 分类结果列表

        Returns:
            统计信息
        """
        stats = {}
        for result in classified_results:
            main_cat = result.get("main_category", "未知")
            if main_cat not in stats:
                stats[main_cat] = {}

            sub_cat = result.get("sub_category", "未知")
            if sub_cat not in stats[main_cat]:
                stats[main_cat][sub_cat] = 0

            stats[main_cat][sub_cat] += 1

        return stats

    


class BotIntent:
    """意图识别（兼容旧接口）"""

    def __init__(self):
        self.classifier = IntentClassifier()

    def classify(self, query: str) -> Dict:
        """
        意图分类接口

        Args:
            query: 用户查询

        Returns:
            分类结果
        """
        return self.classifier.classify_intent(query)
