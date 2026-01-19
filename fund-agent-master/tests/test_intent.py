
import re
import json
from dataclasses import dataclass
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from openai import OpenAI
from typing import List
from app.config.settings import settings

chat_client_bot = chat_client_bot = OpenAI(
    base_url='https://open.bigmodel.cn/api/paas/v4/',
    api_key='05241d9777e74605af95a0f815dbfc01.Z6QJcrmx1vhtyoUH'
)




@dataclass
class IntentResult:
    """意图分类结果"""
    intent: str
    confidence: float
    query: str = ""
    pre_answer: str = ""


class IntentClassifier:
    """意图识别分类器"""

    def __init__(self, client=None):
        """
        初始化意图分类器

        Args:
            client: LLM客户端，默认使用chat_client_bot
        """
        self.client = chat_client_bot
        self.intents = [
            '医疗服务项目目录', '医保退休办理', '个人账户一次性支取办理',
            '辅助生殖医保支付政策', '药品目录', '连续参保机制', '生育津贴待遇',
            '惠厦保', '社保', '转移接续手续办理', '异地就医备案办理',
            '参保长效机制', '退费', '医保账户划拨', '缴费标准', '医疗救助',
            '重复参保处理', '家庭共济办理', '待遇生效时间', '生育津贴办理',
            '参保缴费方式', '其他', '待遇标准', '参保缴费纠纷处理', '大病医保',
            '医疗费用报销办理', '参保对象', '就医使用','参保地为厦门',
            '非厦门参保地'
        ]

    def _build_prompt(self, question: str) -> str:
        """构建提示词"""
        intents_str = ",".join(self.intents)

        prompt = f"""#意图识别
#用户将给你一个提问，请你对其意图进行分类，并进行提问纠错，通意转写，主要意图如下：
{{{intents_str}}}

请严格按照JSON格式输出，包含前3个最可能
1)意图分类intent 
2)置信度 confidence
3)同义转写 query
4)可能答案 pre_answer
例如
问题: 其在厦门市集美区参保，现咨询其父亲是否可以在厦门参保？

输出格式：
```json
{{
  "results": [
    {{
      "intent": "参保对象",
      "confidence": 0.9880,
      "query":"外地户籍人员（如父亲）在厦门是否可以参加城乡居民医保？需要满足什么条件？",
      "pre_answer": "厦门市城乡居民医保参保对象包括本市户籍居民、持有本市居住证的非户籍居民，以及在厦就读的全日制在校学生等。若其父亲为外地户籍，需持有厦门市有效居住证或满足其他规定条件方可参保。"
    }},
    {{
      "intent": "参保缴费方式",
      "confidence": 0.0035,
      "query": "外地户籍人员在厦门参加城乡居民医保怎么缴费",
      "pre_answer": "符合条件的外地户籍人员可凭居住证等材料到居住地所在街道（镇）便民服务中心办理城乡居民医保参保登记，缴费通常通过税务部门提供的线上或线下渠道完成。"
    }},
    {{
      "intent": "重复参保处理",
      "confidence": 0.0010,
      "query": "外地户籍人员在厦门参加城乡居民医保，重复参加医保怎么处理",
      "pre_answer": "根据国家医保政策，不允许重复参保。若其父亲已在外地参加城乡居民医保或职工医保，需先暂停原参保地医保关系，方可按规定在厦门办理参保。"
    }}
  ]
}}
```

请分析以下问题并给出分类结果：
问题: {question}

请严格按照上述JSON格式输出，确保包含results数组，每个结果包含intent和confidence字段。"""

        return prompt

    def _parse_response(self, response: str) -> List[IntentResult]:
        """解析LLM响应"""
        results = []

        # 首先尝试解析JSON格式
        try:
            # 尝试提取JSON代码块
            json_pattern = r'```(?:json)?\s*({.*?})\s*```'
            json_match = re.search(json_pattern, response, re.DOTALL)

            if json_match:
                json_str = json_match.group(1)
            else:
                # 如果没有代码块，尝试直接解析整个响应
                json_str = response.strip()

            # 解析JSON
            data = json.loads(json_str)

            # 提取results数组
            if isinstance(data, dict) and 'results' in data:
                results_list = data['results']
                if isinstance(results_list, list):
                    for item in results_list:
                        if isinstance(item, dict):
                            intent = item.get('intent', '').strip()
                            confidence = float(item.get('confidence', 0))
                            query = item.get('query', '').strip()
                            pre_answer = item.get('pre_answer', '').strip()

                            # 验证意图是否在预定义列表中
                            if intent in self.intents or intent == '其他':
                                results.append(
                                    IntentResult(intent=intent,
                                                 confidence=confidence,
                                                 query=query,
                                                 pre_answer=pre_answer)
                                )

        except (json.JSONDecodeError, KeyError, ValueError, AttributeError) as e:
            print(f"JSON解析失败，尝试正则表达式解析: {e}")

            # 如果JSON解析失败，使用正则表达式作为备用方案
            # 支持原格式：意图 (置信度: 数值)
            pattern = r'([^(]+)\s*\(置信度:\s*([\d.]+)\)'
            matches = re.findall(pattern, response)

            for match in matches:
                intent = match[0].strip()
                confidence = float(match[1])

                # 验证意图是否在预定义列表中
                if intent in self.intents or intent == '其他':
                    results.append(
                        IntentResult(intent=intent,
                                     confidence=confidence,
                                     query="",
                                     pre_answer="")
                    )

            # 如果仍然没有找到匹配结果，尝试其他解析方式
            if not results:
                lines = response.strip().split('\n')
                for line in lines[:3]:  # 只取前3行
                    if '：' in line or ':' in line:
                        parts = re.split(r'[：:]', line, 1)
                        if len(parts) == 2:
                            intent_part = parts[0].strip()
                            confidence_part = parts[1].strip()

                            # 提取置信度数值
                            conf_match = re.search(r'[\d.]+', confidence_part)
                            if conf_match:
                                confidence = float(conf_match.group())
                                intent = intent_part

                                if intent in self.intents or intent == '其他':
                                    results.append(
                                        IntentResult(intent=intent,
                                                     confidence=confidence,
                                                     query="",
                                                     pre_answer="")
                                    )

        # 按置信度排序并返回前3个
        results.sort(key=lambda x: x.confidence, reverse=True)
        return results[:3]

    def classify(self, question: str) -> List[IntentResult]:
        """
        对问题进行意图分类

        Args:
            question: 用户问题

        Returns:
            意图分类结果列表，按置信度降序排列
        """
        prompt = self._build_prompt(question)

        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL or "glm-4.5-air",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500,
                extra_body= {
                'enable_thinking': False,
                "thinking": {
                    "type": "disabled",
                },
            })

            response_text = response.choices[0].message.content or ""
            print(response_text)
            results = self._parse_response(response_text)

            return results

        except Exception as e:
            print(f"意图分类失败: {e}")
            # 返回默认结果
            return [IntentResult(intent='基础', confidence=1.0)]

    def format_results(self, results: List[IntentResult]) -> str:
        """
        格式化输出结果

        Args:
            results: 意图分类结果

        Returns:
            格式化的字符串
        """
        output_lines = []
        for result in results:
            output_lines.append(f"{result.intent} {result.confidence:.4f}")

        return "\n".join(output_lines)


# 示例使用函数
def classify_intent_simple(question: str) -> str:
    """
    简单的意图分类函数，直接返回格式化结果

    Args:
        question: 用户问题

    Returns:
        格式化的意图分类结果字符串
    """
    classifier = IntentClassifier()
    results = classifier.classify(question)
    return classifier.format_results(results)



# 测试示例
if __name__ == "__main__":
    # 创建分类器实例
    classifier = IntentClassifier()

    # 测试问题
    test_question = "其在厦门市集美区参保，现咨询其父亲是否可以在厦门参保？"

    # 进行意图分类
    results = classifier.classify(test_question)
    

    # 输出结果
    print("问题:", test_question)
    print("分类结果:")
    print(classifier.format_results(results))

    # 测试简单函数
    print("\n使用简单函数测试:")
    print(classify_intent_simple("我想了解一下医保报销的流程"))

