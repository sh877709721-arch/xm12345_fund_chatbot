#!/usr/bin/env python3
# 复制表
import psycopg2
import json
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2.extras import Json

def copy_tables():
    # 数据库连接信息
    # 源数据库连接（用于source_schema）
    source_db_params = {
        'host': '121.41.44.149',
        'port': '6432',
        'database': 'etl_data',
        'user': 'chatbot',
        'password': 'dw2We3GoMaRT4y'
    }
    
    # 目标数据库连接（用于target_schema）
    target_db_params = {
        'host': '121.41.44.149',
        'port': '6432',
        'database': 'etl_data',
        'user': 'etl',
        'password': 'dw2We3GoMaRT4yaa'
    }
    
    try:
        # 连接到源数据库
        source_conn = psycopg2.connect(**source_db_params)
        source_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        source_cursor = source_conn.cursor()
        
        # 连接到目标数据库
        target_conn = psycopg2.connect(**target_db_params)
        target_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        target_cursor = target_conn.cursor()
        
        print("Connected to databases successfully.")
        
        # 定义源schema和目标schema
        source_schema = 'medical_insurance'
        target_schema = 'demo_hospital'
        
        # 获取源schema中的所有表名
        source_cursor.execute(f"""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = '{source_schema}'
          AND table_type = 'BASE TABLE';
        """)
        
        # 获取所有表名并排除users和user_roles表
        all_tables = [row[0] for row in source_cursor.fetchall()]
        exclude_tables = ['users', 'user_roles']
        tables = [table for table in all_tables if table not in exclude_tables]
        
        print(f"Found {len(all_tables)} tables in {source_schema}, excluding {len(exclude_tables)} tables, will copy {len(tables)} tables.")
        print(f"Tables to copy: {tables}")
        
        for table in tables:
            print(f"\nProcessing table: {table}")
            
            # 1. 获取源表的创建语句 - 包含用户定义类型的完整信息
            source_cursor.execute(f"""
            SELECT 
                c.column_name,
                CASE 
                    WHEN c.data_type = 'USER-DEFINED' THEN t.typname
                    ELSE c.data_type
                END as actual_data_type,
                c.is_nullable,
                c.column_default
            FROM 
                information_schema.columns c
            LEFT JOIN 
                pg_type t ON c.udt_name = t.typname
            WHERE 
                c.table_schema = '{source_schema}' 
                AND c.table_name = '{table}';
            """)
            columns = source_cursor.fetchall()
            
            # 2. 获取源表的主键信息
            source_cursor.execute(f"""
            SELECT DISTINCT c.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name
            JOIN information_schema.columns c ON c.table_schema = tc.table_schema AND c.table_name = tc.table_name AND c.column_name = ccu.column_name
            WHERE tc.table_schema = '{source_schema}' AND tc.table_name = '{table}' AND tc.constraint_type = 'PRIMARY KEY';
            """)
            primary_keys = [row[0] for row in source_cursor.fetchall()]
            
            # 3. 构建CREATE TABLE语句
            create_table_query = f"CREATE TABLE IF NOT EXISTS {target_schema}.{table} (\n"
            column_defs = []
            for col in columns:
                col_name, actual_data_type, is_nullable, col_default = col
                col_def = f"    {col_name} {actual_data_type}"
                if is_nullable == 'NO':
                    col_def += " NOT NULL"
                if col_default is not None:
                    col_def += f" DEFAULT {col_default}"
                column_defs.append(col_def)
            
            if primary_keys:
                primary_key_clause = f"    PRIMARY KEY ({', '.join(primary_keys)})"
                column_defs.append(primary_key_clause)
            
            create_table_query += ",\n".join(column_defs)
            create_table_query += "\n);"
            
            # 4. 创建目标表
            target_cursor.execute(create_table_query)
            print(f"Created table {target_schema}.{table} (if not exists).")
            
            # 5. 清空目标表（可选，根据需求决定是否保留现有数据）
            truncate_query = f"TRUNCATE TABLE {target_schema}.{table} CASCADE;"
            target_cursor.execute(truncate_query)
            print(f"Truncated table {target_schema}.{table}.")
            
            # 6. 复制数据 - 使用源连接读取数据，然后插入到目标连接
            print(f"Reading data from {source_schema}.{table}...")
            # 先获取源表的所有数据
            source_cursor.execute(f"SELECT * FROM {source_schema}.{table};")
            rows = source_cursor.fetchall()
            print(f"Read {len(rows)} rows from {source_schema}.{table}.")
            
            if rows:
                # 获取列名
                col_names = [desc[0] for desc in source_cursor.description]
                print(f"Columns: {col_names}")
                # 构建INSERT语句
                insert_query = f"INSERT INTO {target_schema}.{table} ({', '.join(col_names)}) VALUES ({', '.join(['%s'] * len(col_names))});"
                print(f"Insert query: {insert_query[:100]}...")  # 只打印前100个字符
                
                # 处理JSON类型数据
                processed_rows = []
                for row in rows:
                    processed_row = []
                    for value in row:
                        if isinstance(value, (dict, list)):
                            # 使用Json适配器处理字典和列表类型
                            processed_row.append(Json(value))
                        else:
                            processed_row.append(value)
                    processed_rows.append(processed_row)
                
                # 批量插入数据
                print("Inserting data...")
                target_cursor.executemany(insert_query, processed_rows)
                print(f"Copied {len(processed_rows)} rows from {source_schema}.{table} to {target_schema}.{table}.")
            else:
                print(f"No data to copy for table {table}.")
            
            # 7. 打印复制的行数
            target_cursor.execute(f"SELECT COUNT(*) FROM {target_schema}.{table};")
            count = target_cursor.fetchone()[0]
            print(f"Total rows in {target_schema}.{table}: {count}")
        
        # 关闭连接
        source_cursor.close()
        source_conn.close()
        target_cursor.close()
        target_conn.close()
        print("\nAll tables copied successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    copy_tables()