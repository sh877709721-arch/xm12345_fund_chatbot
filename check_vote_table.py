from sqlalchemy import create_engine, text
from app.config.settings import settings

# 创建数据库引擎
engine = create_engine(settings.CHAT_POSTGRES_URL)

# 检查 vote_id 列是否是自增主键
with engine.connect() as conn:
    print("检查 vote 表的 vote_id 列结构:")
    result = conn.execute(text("""
        SELECT column_name, data_type, is_identity, identity_generation 
        FROM information_schema.columns 
        WHERE table_name = 'vote' AND column_name = 'vote_id';
    """))
    
    for row in result:
        print(f"列名: {row.column_name}")
        print(f"数据类型: {row.data_type}")
        print(f"是否为自增列: {row.is_identity}")
        print(f"自增生成方式: {row.identity_generation}")
    
    # 查看表的完整结构
    print("\n查看 vote 表的完整结构:")
    result = conn.execute(text("SELECT * FROM vote LIMIT 1;"))
    print(f"表列名: {result.keys()}")
    
    # 尝试直接插入一条记录，看看是否能自动生成主键
    print("\n尝试直接插入一条记录:")
    try:
        conn.execute(text("""
            INSERT INTO vote (message_id, vote_type, feedback) 
            VALUES (1, 'good', 'test') 
            RETURNING vote_id;
        """))
        conn.commit()
        print("插入成功")
    except Exception as e:
        conn.rollback()
        print(f"插入失败: {e}")
