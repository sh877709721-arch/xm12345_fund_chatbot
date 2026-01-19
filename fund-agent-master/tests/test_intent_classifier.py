"""
意图分类器测试文件
"""
# 添加项目路径
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import Mock, patch, MagicMock
from app.core.agents.bot_intent import IntentClassifier, BotIntent


class TestIntentClassifier(unittest.TestCase):
    """意图分类器测试类"""

    def setUp(self):
        """测试前置设置"""
        self.classifier = IntentClassifier()

    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.classifier.rag_search)
        self.assertIsNotNone(self.classifier.client)
        self.assertIsNotNone(self.classifier.intent_categories)

    def test_build_classification_prompt(self):
        """测试提示词构建"""
        query = "测试查询"
        search_results = [
            {
                "question": "测试问题1",
                "answer": "测试答案1" * 50  # 长文本测试截断
            },
            {
                "question": "测试问题2",
                "answer": "测试答案2"
            }
        ]

        prompt = self.classifier._build_classification_prompt(query, search_results)

        self.assertIn("测试查询", prompt)
        self.assertIn("测试问题1", prompt)
        self.assertIn("测试答案1", prompt)
        self.assertIn("职工基本医疗保险", prompt)
        self.assertIn("main_category", prompt)
        self.assertIn("sub_category", prompt)

    def test_build_classification_prompt_empty_results(self):
        """测试空搜索结果的提示词构建"""
        query = "测试查询"
        search_results = []

        prompt = self.classifier._build_classification_prompt(query, search_results)

        self.assertIn("测试查询", prompt)
        self.assertIn("可选类别体系", prompt)
        self.assertNotIn("相关参考信息", prompt)

    @patch('app.core.agents.bot_intent.RAGSearch')
    @patch('app.core.agents.bot_intent.chat_client_bot')
    def test_classify_intent_success(self, mock_client, mock_rag_search):
        """测试成功的意图分类"""
        # 模拟RAG搜索结果
        mock_rag_search.return_value.hybrid_search_with_rerank.return_value = [
            {
                "question": "测试问题",
                "answer": "测试答案",
                "similarity_score": 0.8
            }
        ]

        # 模拟LLM响应
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"main_category": "职工基本医疗保险", "sub_category": "参保缴费", "detail_category": "参保对象", "confidence": 0.9, "reason": "测试成功"}'
        mock_client.chat.completions.create.return_value = mock_response

        # 创建新实例以使用模拟对象
        with patch('app.core.agents.bot_intent.RAGSearch') as mock_rag_class:
            mock_rag_instance = Mock()
            mock_rag_instance.hybrid_search_with_rerank.return_value = [
                {
                    "question": "测试问题",
                    "answer": "测试答案",
                    "similarity_score": 0.8
                }
            ]
            mock_rag_class.return_value = mock_rag_instance

            with patch('app.core.agents.bot_intent.chat_client_bot', mock_client):
                classifier = IntentClassifier()
                result = classifier.classify_intent("测试查询")

        # 验证结果
        self.assertEqual(result['main_category'], '职工基本医疗保险')
        self.assertEqual(result['sub_category'], '参保缴费')
        self.assertEqual(result['detail_category'], '参保对象')
        self.assertEqual(result['confidence'], 0.9)
        self.assertEqual(result['reason'], '测试成功')
        self.assertEqual(result['search_results_count'], 1)

    @patch('app.core.agents.bot_intent.RAGSearch')
    @patch('app.core.agents.bot_intent.chat_client_bot')
    def test_classify_intent_json_parse_error(self, mock_client, mock_rag_search):
        """测试JSON解析错误处理"""
        # 模拟RAG搜索结果
        mock_rag_search.return_value.hybrid_search_with_rerank.return_value = []

        # 模拟无效JSON响应
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "这不是有效的JSON"
        mock_client.chat.completions.create.return_value = mock_response

        # 创建新实例以使用模拟对象
        with patch('app.core.agents.bot_intent.RAGSearch') as mock_rag_class:
            mock_rag_instance = Mock()
            mock_rag_instance.hybrid_search_with_rerank.return_value = []
            mock_rag_class.return_value = mock_rag_instance

            with patch('app.core.agents.bot_intent.chat_client_bot', mock_client):
                classifier = IntentClassifier()
                result = classifier.classify_intent("测试查询")

        # 验证错误处理
        self.assertEqual(result['main_category'], '未识别')
        self.assertEqual(result['confidence'], 0.0)
        self.assertEqual(result['reason'], 'LLM响应解析失败')
        self.assertIn('raw_response', result)

    @patch('app.core.agents.bot_intent.RAGSearch')
    @patch('app.core.agents.bot_intent.chat_client_bot')
    def test_classify_intent_api_error(self, mock_client, mock_rag_search):
        """测试API错误处理"""
        # 模拟API异常
        mock_client.chat.completions.create.side_effect = Exception("API错误")

        # 创建新实例以使用模拟对象
        with patch('app.core.agents.bot_intent.RAGSearch'):
            with patch('app.core.agents.bot_intent.chat_client_bot', mock_client):
                classifier = IntentClassifier()
                result = classifier.classify_intent("测试查询")

        # 验证错误处理
        self.assertEqual(result['main_category'], '错误')
        self.assertEqual(result['confidence'], 0.0)
        self.assertIn("分类过程出现异常", result['reason'])

    def test_batch_classify(self):
        """测试批量分类"""
        queries = ["查询1", "查询2", "查询3"]

        # 模拟classify_intent方法
        self.classifier.classify_intent = Mock(side_effect=[
            {"main_category": "类别1", "confidence": 0.8},
            {"main_category": "类别2", "confidence": 0.9},
            {"main_category": "类别3", "confidence": 0.7}
        ])

        results = self.classifier.batch_classify(queries)

        # 验证结果
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['main_category'], '类别1')
        self.assertEqual(results[1]['main_category'], '类别2')
        self.assertEqual(results[2]['main_category'], '类别3')

    def test_get_category_stats(self):
        """测试分类统计"""
        classified_results = [
            {"main_category": "职工基本医疗保险", "sub_category": "参保缴费"},
            {"main_category": "职工基本医疗保险", "sub_category": "医疗待遇"},
            {"main_category": "职工基本医疗保险", "sub_category": "参保缴费"},
            {"main_category": "城乡居民医疗保险", "sub_category": "参保缴费"},
        ]

        stats = self.classifier.get_category_stats(classified_results)

        # 验证统计结果
        self.assertEqual(stats["职工基本医疗保险"]["参保缴费"], 2)
        self.assertEqual(stats["职工基本医疗保险"]["医疗待遇"], 1)
        self.assertEqual(stats["城乡居民医疗保险"]["参保缴费"], 1)


class TestBotIntent(unittest.TestCase):
    """BotIntent兼容接口测试"""

    def setUp(self):
        """测试前置设置"""
        self.bot_intent = BotIntent()

    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.bot_intent.classifier)

    @patch('app.core.agents.bot_intent.IntentClassifier')
    def test_classify(self, mock_classifier_class):
        """测试classify方法"""
        # 模拟分类器
        mock_classifier = Mock()
        mock_classifier.classify_intent.return_value = {
            "main_category": "测试分类",
            "confidence": 0.8
        }
        mock_classifier_class.return_value = mock_classifier

        bot_intent = BotIntent()
        result = bot_intent.classify("测试查询")

        # 验证调用和结果
        mock_classifier.classify_intent.assert_called_once_with("测试查询")
        self.assertEqual(result["main_category"], "测试分类")


if __name__ == '__main__':
    # 运行测试
    unittest.main()