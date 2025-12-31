"""
数据库RAG助手使用示例

演示如何使用DatabaseAssistant进行基于数据库的问答。
支持MySQL、PostgreSQL、MongoDB等多种数据库类型。
"""

import json
import logging
from typing import Dict, Any

from app.core.del_database import DatabaseAssistant
from app.core.del_database.config import (
    get_db_config_template,
    validate_db_config,
    get_create_table_sql,
    load_config_from_env
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_mysql_assistant() -> DatabaseAssistant:
    """创建MySQL数据库助手"""
    db_config = {
        'type': 'mysql',
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': 'your_password',
        'database': 'medical_db',
        'table': 'documents',
        'content_field': 'content',
        'title_field': 'title',
        'id_field': 'id',
        'timestamp_field': 'created_at'
    }

    # 创建数据库助手
    assistant = DatabaseAssistant(
        llm={'model': 'qwen-plus-latest'},
        name='医保查询助手',
        description='基于MySQL数据库的医保政策查询助手，支持从数据库中检索相关医保信息。',
        db_config=db_config,
        rag_cfg={
            'max_ref_token': 4000,
            'rag_keygen_strategy': 'SplitQueryThenGenKeyword',
            'rag_searchers': ['database_retrieval']
        }
    )

    return assistant


def create_postgresql_assistant() -> DatabaseAssistant:
    """创建PostgreSQL数据库助手"""
    db_config = {
        'type': 'postgresql',
        'host': 'localhost',
        'port': 5432,
        'user': 'postgres',
        'password': 'your_password',
        'database': 'medical_db',
        'table': 'documents',
        'content_field': 'content',
        'title_field': 'title',
        'id_field': 'id',
        'timestamp_field': 'created_at'
    }

    assistant = DatabaseAssistant(
        llm={'model': 'qwen-plus-latest'},
        name='PostgreSQL医保助手',
        description='基于PostgreSQL数据库的智能问答助手',
        db_config=db_config
    )

    return assistant


def create_mongodb_assistant() -> DatabaseAssistant:
    """创建MongoDB数据库助手"""
    db_config = {
        'type': 'mongodb',
        'host': 'localhost',
        'port': 27017,
        'database': 'medical_db',
        'collection': 'documents'
    }

    assistant = DatabaseAssistant(
        llm={'model': 'qwen-plus-latest'},
        name='MongoDB医保助手',
        description='基于MongoDB的智能问答助手',
        db_config=db_config
    )

    return assistant


def example_simple_query():
    """简单查询示例"""
    logger.info("=== 简单查询示例 ===")

    # 创建MySQL助手
    assistant = create_mysql_assistant()

    # 模拟用户查询
    from qwen_agent.llm.schema import Message

    messages = [Message(
        role='user',
        content='请问厦门市医保报销比例是多少？'
    )]

    try:
        # 执行查询
        responses = list(assistant._run(messages, lang='zh'))

        # 输出结果
        for response_batch in responses:
            for message in response_batch:
                if message.role == 'assistant':
                    print(f"助手回复: {message.content}")
                    break

    except Exception as e:
        logger.error(f"查询失败: {e}")


def example_advanced_query():
    """高级查询示例"""
    logger.info("=== 高级查询示例 ===")

    assistant = create_mysql_assistant()

    from qwen_agent.llm.schema import Message

    # 复杂查询
    messages = [Message(
        role='user',
        content='我想了解异地就医备案流程和需要准备的材料'
    )]

    try:
        # 使用额外参数进行查询
        responses = list(assistant._run(
            messages=messages,
            lang='zh',
            limit=5,
            keywords=['异地就医', '备案', '材料', '流程']
        ))

        for response_batch in responses:
            for message in response_batch:
                if message.role == 'assistant':
                    print(f"助手回复: {message.content}")
                    break

    except Exception as e:
        logger.error(f"查询失败: {e}")


def example_openai_format():
    """OpenAI格式响应示例"""
    logger.info("=== OpenAI格式响应示例 ===")

    assistant = create_mysql_assistant()

    from qwen_agent.llm.schema import Message

    messages = [Message(
        role='user',
        content='医保个人账户如何使用？'
    )]

    try:
        # 获取OpenAI格式的流式响应
        for chunk in assistant._run_openai_format(messages, lang='zh'):
            print(chunk, end='')

    except Exception as e:
        logger.error(f"OpenAI格式响应失败: {e}")


def example_config_management():
    """配置管理示例"""
    logger.info("=== 配置管理示例 ===")

    # 获取配置模板
    mysql_template = get_db_config_template('mysql')
    print("MySQL配置模板:")
    print(json.dumps(mysql_template, indent=2, ensure_ascii=False))

    # 验证配置
    is_valid = validate_db_config(mysql_template)
    print(f"配置验证结果: {'有效' if is_valid else '无效'}")

    # 获取建表SQL
    create_sql = get_create_table_sql('mysql')
    print("\nMySQL建表SQL:")
    print(create_sql)


def example_health_check():
    """健康检查示例"""
    logger.info("=== 健康检查示例 ===")

    assistant = create_mysql_assistant()

    try:
        # 执行健康检查
        health_info = assistant.health_check()
        print("健康检查结果:")
        print(json.dumps(health_info, indent=2, ensure_ascii=False))

        # 获取助手信息
        assistant_info = assistant.get_assistant_info()
        print("\n助手信息:")
        print(json.dumps(assistant_info, indent=2, ensure_ascii=False))

    except Exception as e:
        logger.error(f"健康检查失败: {e}")


def example_web_ui():
    """Web UI集成示例"""
    logger.info("=== Web UI集成示例 ===")

    # 创建助手
    assistant = create_mysql_assistant()

    try:
        from qwen_agent.gui.web_ui import WebUI

        # Web UI配置
        chatbot_config = {
            'prompt.suggestions': [
                {'text': '查询医保报销比例'},
                {'text': '异地就医备案流程'},
                {'text': '个人账户使用规则'},
                {'text': '医保缴费标准'}
            ]
        }

        # 启动Web UI
        web_ui = WebUI(assistant, chatbot_config=chatbot_config)
        print("Web UI已启动，请访问 http://localhost:7860")
        web_ui.run()

    except ImportError:
        logger.error("WebUI模块未安装，请安装相关依赖")
    except Exception as e:
        logger.error(f"Web UI启动失败: {e}")


def example_environment_config():
    """环境变量配置示例"""
    logger.info("=== 环境变量配置示例 ===")

    # 从环境变量加载MySQL配置
    try:
        mysql_config = load_config_from_env('mysql')
        print("从环境变量加载的MySQL配置:")
        print(json.dumps(mysql_config, indent=2, ensure_ascii=False))

        # 如果环境变量中有有效配置，创建助手
        if validate_db_config(mysql_config):
            assistant = DatabaseAssistant(
                llm={'model': 'qwen-plus-latest'},
                name='环境配置助手',
                db_config=mysql_config
            )
            print("使用环境变量配置的助手创建成功")
        else:
            print("环境变量配置不完整，使用默认配置")

    except Exception as e:
        logger.error(f"环境变量配置加载失败: {e}")


def main():
    """主函数，运行所有示例"""
    print("数据库RAG助手使用示例")
    print("=" * 50)

    # 选择要运行的示例
    examples = {
        '1': ('简单查询', example_simple_query),
        '2': ('高级查询', example_advanced_query),
        '3': ('OpenAI格式响应', example_openai_format),
        '4': ('配置管理', example_config_management),
        '5': ('健康检查', example_health_check),
        '6': ('环境变量配置', example_environment_config),
        '7': ('Web UI集成', example_web_ui),
    }

    print("请选择要运行的示例:")
    for key, (name, _) in examples.items():
        print(f"{key}. {name}")

    choice = input("请输入选择 (1-7): ").strip()

    if choice in examples:
        name, func = examples[choice]
        print(f"\n运行示例: {name}")
        print("-" * 30)
        func()
    else:
        print("无效选择，运行默认示例...")
        example_config_management()


if __name__ == '__main__':
    main()