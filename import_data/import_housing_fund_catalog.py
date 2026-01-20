#!/usr/bin/env python3
import pandas as pd
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def import_housing_fund_catalog():
    # 数据库连接信息
    db_params = {
        'host': '121.41.44.149',
        'port': '6432',
        'database': 'etl_data',
        'user': 'etl',
        'password': 'dw2We3GoMaRT4yaa'
    }
    
    # Excel文件路径
    excel_file = '/home/hello/fund-agent/2026.1.9公积金知识三级分类目录.xlsx'
    
    try:
        # 1. 读取Excel数据
        print(f"Reading Excel file: {excel_file}")
        df = pd.read_excel(excel_file)
        print(f"Excel data loaded successfully. Total rows: {len(df)}")
        
        # 2. 连接到数据库
        conn = psycopg2.connect(**db_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        print("Connected to database successfully.")
        
        # 3. 准备插入数据
        schema = 'ods'
        table = 'knowledge_catalog_v1'
        
        # 清空目标表（可选，根据需求决定是否保留现有数据）
        # cursor.execute(f"TRUNCATE TABLE {schema}.{table} CASCADE;")
        # print(f"Truncated table {schema}.{table}.")
        
        # 4. 插入数据
        inserted_count = 0
        for index, row in df.iterrows():
            # 获取字段值
            category_level_1 = row['一级'] if pd.notna(row['一级']) else None
            category_level_2 = row['二级'] if pd.notna(row['二级']) else None
            category_level_3 = row['三级'] if pd.notna(row['三级']) else None
            
            # 构建插入SQL
            insert_query = f"""
            INSERT INTO {schema}.{table} (category_level_1, category_level_2, category_level_3)
            VALUES (%s, %s, %s)
            """
            
            # 执行插入
            cursor.execute(insert_query, (category_level_1, category_level_2, category_level_3))
            inserted_count += 1
            
            if inserted_count % 100 == 0:
                print(f"Inserted {inserted_count} rows...")
        
        print(f"\nInserted total {inserted_count} rows into {schema}.{table} table.")
        
        # 5. 关闭连接
        cursor.close()
        conn.close()
        print("Database connection closed.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import_housing_fund_catalog()