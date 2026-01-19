"""
测试 AgentFactory 功能
验证新的统一入口是否正常工作
"""

def test_new_agents_import():
    """测试新的导入方式"""
    print("=== 测试新的导入方式 ===")
    try:
        from app.core.agents import agent_factory, AgentFactory, get_llm_config
        print("✅ 新的导入方式成功")

        # 测试 LLM 配置
        llm_config = get_llm_config()
        print(f"✅ LLM 配置获取成功: {llm_config['model']}")

        return True
    except Exception as e:
        print(f"❌ 新的导入方式失败: {e}")
        return False


def test_agent_factory_basic():
    """测试工厂基本功能"""
    print("\n=== 测试工厂基本功能 ===")
    try:
        from app.core.agents import agent_factory

        # 测试获取机器人
        bot = agent_factory.get_agent('bot')
        print(f"✅ 获取 bot 成功: {bot.__class__.__name__}")

        rag_bot = agent_factory.get_agent('rag_bot')
        print(f"✅ 获取 rag_bot 成功: {rag_bot.__class__.__name__}")

        qwen_rag_bot = agent_factory.get_agent('qwen_rag_bot')
        print(f"✅ 获取 qwen_rag_bot 成功: {qwen_rag_bot.__class__.__name__}")

        return True
    except Exception as e:
        print(f"❌ 工厂基本功能测试失败: {e}")
        return False


def test_agent_factory_features():
    """测试工厂高级功能"""
    print("\n=== 测试工厂高级功能 ===")
    try:
        from app.core.agents import agent_factory

        # 测试字典式访问
        bot = agent_factory['bot']
        print("✅ 字典式访问成功")

        # 测试列表功能
        agents = agent_factory.list_agents()
        print(f"✅ 获取机器人列表成功: {len(agents)} 个机器人")

        # 测试包含检查
        has_bot = 'bot' in agent_factory
        print(f"✅ 包含检查成功: 'bot' 存在 = {has_bot}")

        # 测试语义化别名
        medical_agent = agent_factory.get_agent('medical_agent')
        print(f"✅ 语义化别名成功: {medical_agent.__class__.__name__}")

        # 测试安全获取
        safe_agent = agent_factory.get_agent_safe('nonexistent', 'bot')
        print("✅ 安全获取成功")

        # 测试错误处理
        try:
            agent_factory.get_agent('nonexistent')
            print("❌ 错误处理失败：应该抛出 KeyError")
            return False
        except KeyError:
            print("✅ 错误处理成功：正确抛出 KeyError")

        return True
    except Exception as e:
        print(f"❌ 高级功能测试失败: {e}")
        return False


def test_backward_compatibility():
    """测试向后兼容性"""
    print("\n=== 测试向后兼容性 ===")
    try:
        # 测试原有导入方式
        from app.core.agent import bot, rag_bot, qwen_rag_bot
        print("✅ 原有导入方式成功（带废弃警告）")

        # 测试原有导入的机器人是否可用
        print(f"✅ bot 类型: {bot.__class__.__name__}")
        print(f"✅ rag_bot 类型: {rag_bot.__class__.__name__}")
        print(f"✅ qwen_rag_bot 类型: {qwen_rag_bot.__class__.__name__}")

        return True
    except Exception as e:
        print(f"❌ 向后兼容性测试失败: {e}")
        return False


def test_agent_info():
    """测试机器人信息获取"""
    print("\n=== 测试机器人信息获取 ===")
    try:
        from app.core.agents import agent_factory

        for agent_key in ['bot', 'rag_bot', 'qwen_rag_bot']:
            info = agent_factory.get_agent_info(agent_key)
            print(f"✅ {agent_key}: {info['class']} - {info['description']}")

        return True
    except Exception as e:
        print(f"❌ 机器人信息获取失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("开始测试 AgentFactory 功能...\n")

    tests = [
        test_new_agents_import,
        test_agent_factory_basic,
        test_agent_factory_features,
        test_backward_compatibility,
        test_agent_info
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print(f"\n=== 测试结果 ===")
    print(f"通过: {passed}/{total}")
    print(f"成功率: {passed/total*100:.1f}%")

    if passed == total:
        print("🎉 所有测试通过！AgentFactory 可以正常使用。")
    else:
        print("⚠️  部分测试失败，请检查配置和依赖。")


if __name__ == "__main__":
    main()