#!/usr/bin/env python3
"""
数据库调试脚本
检查反馈表是否存在，如果不存在则创建
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config.database import engine, Base
from app.model.feedback import Feedback
from sqlalchemy import inspect, text

def check_and_create_table():
    """检查并创建反馈表"""
    inspector = inspect(engine)

    print("检查数据库表...")
    tables = inspector.get_table_names()
    print(f"当前数据库中的表: {tables}")

    if 'feedback' not in tables:
        print("❌ feedback 表不存在，正在创建...")
        try:
            # 创建所有表
            Base.metadata.create_all(bind=engine)
            print("✅ feedback 表创建成功！")
        except Exception as e:
            print(f"❌ 创建表失败: {e}")
            return False
    else:
        print("✅ feedback 表已存在")

        # 检查表结构
        columns = inspector.get_columns('feedback')
        print("表结构:")
        for column in columns:
            print(f"  - {column['name']}: {column['type']}")

    return True

def test_db_connection():
    """测试数据库连接"""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ 数据库连接正常")
            return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

def test_feedback_creation():
    """测试反馈创建"""
    try:
        from app.config.database import get_db
        from app.service.feedback import FeedbackService
        from app.schema.feedback import FeedbackCreate

        # 获取数据库会话
        db = next(get_db())

        # 创建测试反馈
        test_feedback = FeedbackCreate(
            content="这是一个测试反馈",
            phone="13800138000",
            images=None
        )

        # 创建服务实例
        service = FeedbackService(db)

        # 尝试创建反馈
        feedback = service.create_feedback(test_feedback)
        print(f"✅ 测试反馈创建成功，ID: {feedback.id}")

        return True

    except Exception as e:
        print(f"❌ 测试反馈创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== 数据库调试开始 ===")

    # 1. 测试数据库连接
    if not test_db_connection():
        print("❌ 数据库连接失败，退出")
        sys.exit(1)

    # 2. 检查并创建表
    if not check_and_create_table():
        print("❌ 表创建失败，退出")
        sys.exit(1)

    # 3. 测试反馈创建
    if test_feedback_creation():
        print("=== 所有测试通过 ===")
    else:
        print("=== 测试失败 ===")
        sys.exit(1)