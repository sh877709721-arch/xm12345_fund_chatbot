"""
AgentFactory 使用示例
展示如何使用统一的机器人工厂类
"""

from app.core.agents import agent_factory, AgentFactory


def basic_usage_example():
    """基本使用示例"""
    print("=== 基本使用示例 ===")

    # 1. 通过 get_agent 方法获取机器人
    bot = agent_factory.get_agent('bot')
    print(f"获取到的机器人: {bot.__class__.__name__}")

    # 2. 通过字典式访问获取机器人
    medical_agent = agent_factory['medical_agent']
    print(f"医疗助手: {medical_agent.__class__.__name__}")

    # 3. 安全获取机器人（不存在时返回默认值）
    unknown_agent = agent_factory.get_agent_safe('unknown_agent', 'default')
    print(f"安全获取机器人: {unknown_agent.__class__.__name__}")


def available_agents_example():
    """查看可用机器人列表"""
    print("\n=== 可用机器人列表 ===")

    # 获取所有可用机器人的键名
    agents = agent_factory.list_agents()
    print(f"所有可用机器人: {agents}")

    # 获取特定机器人的详细信息
    for agent_key in ['bot', 'rag_bot', 'qwen_rag_bot']:
        info = agent_factory.get_agent_info(agent_key)
        print(f"{info['key']}: {info['description']}")


def comparison_with_old_method():
    """与原有方法的对比"""
    print("\n=== 使用方式对比 ===")

    # 原有方式（仍然支持）
    print("原有导入方式:")
    print("from app.core.agent import bot, rag_bot, qwen_rag_bot")

    # 新的统一方式
    print("\n新的统一入口方式:")
    print("from app.core.agent import agent_factory")
    print("bot = agent_factory.get_agent('bot')")
    print("rag_bot = agent_factory.get_agent('rag_bot')")
    print("qwen_rag_bot = agent_factory.get_agent('qwen_rag_bot')")

    # 语义化访问
    print("\n语义化访问方式:")
    print("medical_agent = agent_factory.get_agent('medical_agent')  # 同 bot")
    print("assistant = agent_factory.get_agent('assistant')          # 同 rag_bot")
    print("qwen_agent = agent_factory.get_agent('qwen_agent')      # 同 qwen_rag_bot")


def error_handling_example():
    """错误处理示例"""
    print("\n=== 错误处理示例 ===")

    try:
        # 尝试获取不存在的机器人
        agent_factory.get_agent('nonexistent_agent')
    except KeyError as e:
        print(f"捕获错误: {e}")

    # 安全的方式（不会抛出异常）
    agent = agent_factory.get_agent_safe('nonexistent_agent', 'bot')
    print(f"安全获取，返回默认机器人: {agent.__class__.__name__}")


def factory_features_example():
    """工厂特性示例"""
    print("\n=== 工厂特性示例 ===")

    # 检查机器人是否存在
    print(f"'bot' 是否存在: {'bot' in agent_factory}")
    print(f"'unknown' 是否存在: {'unknown' in agent_factory}")

    # 工厂的字符串表示
    print(f"工厂信息: {agent_factory}")

    # 单例模式验证
    factory1 = AgentFactory()
    factory2 = AgentFactory()
    print(f"两个工厂实例是否相同: {factory1 is factory2}")


def practical_usage_in_function():
    """在实际函数中的使用示例"""
    def get_answer_for_query(query: str, agent_type: str = 'bot'):
        """
        根据查询类型选择合适的机器人来回答

        Args:
            query: 用户查询
            agent_type: 机器人类型
        """
        try:
            # 根据类型获取机器人
            agent = agent_factory.get_agent(agent_type)

            # 这里可以调用实际的机器人方法
            # response = agent.answer(query)

            return f"使用 {agent.__class__.__name__} 处理查询: {query}"
        except KeyError as e:
            return f"机器人类型错误: {e}"

    print("\n=== 实际使用示例 ===")
    print(get_answer_for_query("医保报销流程是什么？", 'bot'))
    print(get_answer_for_query("今天天气怎么样？", 'assistant'))
    print(get_answer_for_query("测试查询", 'unknown_agent'))


if __name__ == "__main__":
    # 运行所有示例
    basic_usage_example()
    available_agents_example()
    comparison_with_old_method()
    error_handling_example()
    factory_features_example()
    practical_usage_in_function()