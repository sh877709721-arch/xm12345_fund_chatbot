"""Create feedback table

Revision ID: 001_create_feedback_table
Revises:
Create Date: 2025-12-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_create_feedback_table'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """创建反馈表"""
    # 创建 feedback 表
    op.create_table('feedback',
        sa.Column('id', postgresql.BIGINT(), autoincrement=True, nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('images', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('phone', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=255), nullable=False, server_default='A'),
        sa.Column('created_time', sa.DateTime(), nullable=True),
        sa.Column('updated_time', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 创建索引
    op.create_index(op.f('ix_feedback_status'), 'feedback', ['status'], unique=False)
    op.create_index(op.f('ix_feedback_created_time'), 'feedback', ['created_time'], unique=False)

    # 创建触发器函数（用于自动更新 updated_time）
    op.execute("""
        CREATE OR REPLACE FUNCTION update_feedback_updated_time()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_time = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)

    # 创建触发器
    op.execute("""
        CREATE TRIGGER trigger_feedback_updated_time
            BEFORE UPDATE ON feedback
            FOR EACH ROW
            EXECUTE FUNCTION update_feedback_updated_time();
    """)


def downgrade():
    """删除反馈表"""
    # 删除触发器
    op.execute("DROP TRIGGER IF EXISTS trigger_feedback_updated_time ON feedback")

    # 删除触发器函数
    op.execute("DROP FUNCTION IF EXISTS update_feedback_updated_time()")

    # 删除索引
    op.drop_index(op.f('ix_feedback_created_time'), table_name='feedback')
    op.drop_index(op.f('ix_feedback_status'), table_name='feedback')

    # 删除表
    op.drop_table('feedback')