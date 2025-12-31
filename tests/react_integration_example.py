#!/usr/bin/env python3
"""
ReAct框架集成示例
展示如何使用增强的意图识别工具进行智能对话
"""

import json
from dataclasses import dataclass
from typing import Optional

# 模拟MCP工具调用
@dataclass
class MockMCPResponse:
    """模拟MCP工具响应"""
    success: bool
    data: dict

def mock_recognize_user_intent(query: str) -> MockMCPResponse:
    """模拟调用MCP工具recognize_user_intent"""
    # 这里直接调用简化版识别器来演示
    from test_intent_simple import SimpleIntentRecognizer

    recognizer = SimpleIntentRecognizer()
    result = recognizer.recognize_intent(query)

    return MockMCPResponse(
        success=True,
        data={
            "first_level": result.first_level,
            "second_level": result.second_level,
            "third_level": result.third_level,
            "confidence": result.confidence,
            "action": result.action,
            "rewritten_query": result.rewritten_query,
            "needs_clarification": result.needs_clarification,
            "clarification_question": result.clarification_question,
            "timestamp": "2025-01-15T10:00:00"
        }
    )

class ReActAgent:
    """ReAct风格的智能对话代理"""

    def __init__(self):
        self.conversation_context = []
        self.user_slots = {}  # 存储已确认的用户信息槽位

    def think(self, query: str) -> str:
        """思考步骤：分析用户意图"""
        print(f"🤔 Thought: 用户说: '{query}'")

        # 调用意图识别工具
        intent_result = mock_recognize_user_intent(query)

        if not intent_result.success:
            return f"❌ 抱歉，意图识别失败: {intent_result.data}"

        data = intent_result.data
        intent = f"{data['first_level']} > {data['second_level']} > {data['third_level']}"

        print(f"   识别意图: {intent}")
        print(f"   置信度: {data['confidence']}")

        # 更新对话上下文
        self.conversation_context.append({
            "user_query": query,
            "intent": intent,
            "needs_clarification": data['needs_clarification'],
            "clarification_question": data['clarification_question']
        })

        # 决策
        if data['needs_clarification']:
            print(f"   决策: 需要更多信息，准备反问用户")
            return data['clarification_question']
        else:
            print(f"   决策: 信息充足，可以直接回答")
            return self._generate_answer(data)

    def _generate_answer(self, intent_data: dict) -> str:
        """根据意图生成答案"""
        action = intent_data['action']
        first_level = intent_data['first_level']
        third_level = intent_data['third_level']

        # 这里可以接入知识库或其他MCP工具
        answers = {
            "医疗费用报销办理": f"""
✅ **医疗费用报销办理指南**

**基本流程:**
1. 准备相关材料（发票、病历、费用清单等）
2. 到医保经办机构或线上平台提交申请
3. 等待审核（通常5-10个工作日）
4. 审核通过后费用直接划拨到指定账户

**注意事项:**
- 费用需在医保目录范围内
- 保留好所有原始票据和单据
- 申请时限一般为费用发生后2年内

需要了解具体材料清单或线上操作步骤吗？
            """,

            "异地就医备案办理": f"""
✅ **异地就医备案办理指南**

**办理方式:**
1. **线上备案**: 通过国家医保服务平台APP或小程序
2. **线下备案**: 到参保地医保经办机构办理
3. **电话备案**: 拨打参保地医保服务热线

**所需材料:**
- 医保卡/电子医保凭证
- 身份证
- 转诊证明（如适用）
- 异地就医备案申请表

**生效时间**: 备案后即时生效

需要了解具体的线上操作流程吗？
            """,

            "缴费标准": f"""
✅ **医保缴费标准**

根据您的情况，以下是相关缴费信息：

**职工医保:**
- 单位缴纳: 工资基数的8-10%
- 个人缴纳: 工资基数的2%
- 划入个人账户: 约2%

**居民医保:**
- 年度缴费: 300-600元（各地不同）
- 政府补贴: 600-1000元

**灵活就业人员:**
- 可选择职工医保或居民医保
- 缴费基数可在当地平均工资60%-300%间选择

需要了解您所在地区的具体缴费基数吗？
            """,

            "生育津贴待遇": f"""
✅ **生育津贴申领指南**

**申领条件:**
- 在职参保且连续缴费满10个月
- 符合计划生育政策
- 生育时正常参保

**津贴计算:**
- 津贴 = 单位上年度月均工资 ÷ 30 × 产假天数
- 顺产: 98天，剖腹产: 113天
- 多胞胎每多一个婴儿增加15天

**申领材料:**
- 出生医学证明
- 生育服务证
- 身份证和医保卡
- 银行卡

需要了解具体的申请流程或材料准备吗？
            """,

            "家庭共济办理": f"""
✅ **家庭共济办理指南**

**共济范围:**
- 配偶、父母、子女
- 被共济人需参加基本医保

**办理方式:**
1. **线上办理**: 通过医保服务平台
2. **线下办理**: 到医保经办机构

**所需材料:**
- 申请人医保卡
- 共济关系证明（结婚证、户口本等）
- 被共济人医保信息

**使用规则:**
- 资金从主账户划拨
- 用于家庭成员的医疗费用
- 可随时终止共济关系

需要了解具体的线上操作步骤吗？
            """
        }

        default_answer = f"""
✅ **{third_level}**

我理解您想了解关于{third_level}的问题。基于您的描述，我可以为您提供相关信息。

如果您需要更详细的信息或有其他具体问题，请随时告诉我。
        """

        return answers.get(third_level, default_answer)

    def act(self, query: str) -> str:
        """动作步骤：执行思考并返回结果"""
        print("💭 Action: recognize_user_intent")

        # 执行意图识别
        result = self.think(query)

        print("✅ Action: generate_response")
        return result

    def update_slots(self, user_response: str) -> None:
        """更新用户槽位信息"""
        # 简单的槽位更新逻辑
        if any(kw in user_response.lower() for kw in ["门诊", "住院"]):
            self.user_slots["就医类型"] = user_response
        elif any(kw in user_response.lower() for kw in ["北京", "上海", "厦门"]):
            self.user_slots["就医地"] = user_response
        elif any(kw in user_response.lower() for kw in ["职工", "居民"]):
            self.user_slots["参保类型"] = user_response

    def chat(self, user_query: str) -> str:
        """完整对话流程"""
        print(f"\n{'='*60}")
        print(f"👤 用户: {user_query}")
        print(f"{'='*60}")

        # 如果这是对澄清问题的回应，先更新槽位
        if self.conversation_context and self.conversation_context[-1]["needs_clarification"]:
            self.update_slots(user_query)
            print(f"📝 已更新用户信息槽位: {self.user_slots}")

        # 执行ReAct流程
        response = self.act(user_query)

        print(f"🤖 助手: {response}")
        print(f"{'='*60}\n")

        return response

def demo_react_integration():
    """演示ReAct框架集成"""
    print("🎯 ReAct框架集成演示")
    print("展示意图识别工具如何支持智能反问和对话")

    agent = ReActAgent()

    # 模拟对话场景
    conversations = [
        "怎么报销？",  # 需要澄清就医类型
        "是门诊费用",  # 用户回应澄清
        "我想去上海看病需要备案吗？",  # 完整信息
        "生育津贴怎么申请？",  # 需要澄清性别和在职状态
        "女职工在职期间",  # 用户回应澄清
        "家庭共济要怎么办理",  # 需要澄清家庭关系
    ]

    for query in conversations:
        try:
            agent.chat(query)
            input("按Enter继续下一个对话...")
        except KeyboardInterrupt:
            print("\n演示结束")
            break
        except Exception as e:
            print(f"❌ 对话出错: {e}")

def main():
    """主函数"""
    print("🚀 医保意图识别ReAct集成演示")
    print("展示如何使用增强的意图识别工具支持智能对话")

    try:
        demo_react_integration()
    except Exception as e:
        print(f"❌ 演示过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()