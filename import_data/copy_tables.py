#!/usr/bin/env python3
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def copy_tables():
    # 数据库连接信息
    db_params = {
        'host': '121.41.44.149',
        'port': '6432',
        'database': 'etl_data',
        'user': 'chatbot',
        'password': 'dw2We3GoMaRT4y'
    }
    
    try:
        # 连接到数据库
        conn = psycopg2.connect(**db_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("Connected to database successfully.")
        
        # 定义源schema和目标schema
        source_schema = 'medical_insurance'
        target_schema = 'housing_fund'
        
        # 获取源schema中的所有表名
        cursor.execute(f"""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = '{source_schema}'
          AND table_type = 'BASE TABLE';
        """)
        
        # 获取所有表名并排除users和user_roles表
        all_tables = [row[0] for row in cursor.fetchall()]
        exclude_tables = ['users', 'user_roles']
        tables = [table for table in all_tables if table not in exclude_tables]
        
        print(f"Found {len(all_tables)} tables in {source_schema}, excluding {len(exclude_tables)} tables, will copy {len(tables)} tables.")
        print(f"Tables to copy: {tables}")
        
        for table in tables:
            print(f"\nProcessing table: {table}")
            
            # 1. 创建目标表（如果不存在）
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {target_schema}.{table} (
                LIKE {source_schema}.{table} INCLUDING ALL
            );
            """
            cursor.execute(create_table_query)
            print(f"Created table {target_schema}.{table} (if not exists).")
            
            # 2. 清空目标表（可选，根据需求决定是否保留现有数据）
            truncate_query = f"TRUNCATE TABLE {target_schema}.{table} CASCADE;"
            cursor.execute(truncate_query)
            print(f"Truncated table {target_schema}.{table}.")
            
            # 3. 复制数据
            copy_query = f"""
            INSERT INTO {target_schema}.{table}
            SELECT * FROM {source_schema}.{table};
            """
            cursor.execute(copy_query)
            print(f"Copied data from {source_schema}.{table} to {target_schema}.{table}.")
            
            # 4. 打印复制的行数
            cursor.execute(f"SELECT COUNT(*) FROM {target_schema}.{table};")
            count = cursor.fetchone()[0]
            print(f"Total rows in {target_schema}.{table}: {count}")
        
        # 关闭连接
        cursor.close()
        conn.close()
        print("\nAll tables copied successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    copy_tables()