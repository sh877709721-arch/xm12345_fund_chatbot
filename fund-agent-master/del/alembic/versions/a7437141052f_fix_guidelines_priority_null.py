"""fix guidelines priority null values

Revision ID: a7437141052f
Revises: c8b0fc89697d
Create Date: 2026-01-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision: str = 'a7437141052f'
down_revision: Union[str, Sequence[str], None] = 'c8b0fc89697d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    升级：修复 guidelines 表中 priority 字段的 NULL 值问题

    步骤：
    1. 为所有 NULL priority 设置默认值 1
    2. 添加 NOT NULL 约束
    3. 添加 DEFAULT 1 约束
    """

    # 步骤1：为所有 NULL priority 设置默认值
    op.execute(text("""
        UPDATE chatbot.guidelines
        SET priority = 1
        WHERE priority IS NULL
    """))
    op.execute(text("""
        COMMENT ON TABLE chatbot.guidelines IS '已修复所有 priority NULL 值，设置为默认值 1'
    """))

    # 步骤2：添加 NOT NULL 约束
    op.execute(text("""
        ALTER TABLE chatbot.guidelines
        ALTER COLUMN priority
        SET NOT NULL
    """))

    # 步骤3：添加默认值（防止未来插入时遗漏）
    op.execute(text("""
        ALTER TABLE chatbot.guidelines
        ALTER COLUMN priority
        SET DEFAULT 1
    """))

    op.execute(text("""
        COMMENT ON COLUMN chatbot.guidelines.priority IS '优先级(0-9999, 默认1, 越大优先级越高)'
    """))


def downgrade() -> None:
    """
    降级：移除约束（回滚方案）

    注意：此操作不会将已设置为 1 的数据恢复为 NULL
    """
    # 移除默认值
    op.execute(text("""
        ALTER TABLE chatbot.guidelines
        ALTER COLUMN priority
        DROP DEFAULT
    """))

    # 移除 NOT NULL 约束
    op.execute(text("""
        ALTER TABLE chatbot.guidelines
        ALTER COLUMN priority
        DROP NOT NULL
    """))

    op.execute(text("""
        COMMENT ON COLUMN chatbot.guidelines.priority IS '优先级'
    """))
