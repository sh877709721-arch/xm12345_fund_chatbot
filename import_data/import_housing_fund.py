# 从ods源数据库导入公积金目录到目标数据库housing_fund.knowledge_catalog
import psycopg2

def import_housing_fund_catalog():
    # 源数据库连接信息
    source_db_params = {
        'host': '121.41.44.149',
        'port': 6432,
        'database': 'etl_data',
        'user': 'etl',
        'password': 'dw2We3GoMaRT4yaa'
    }
    
    # 目标数据库连接信息
    target_db_params = {
        'host': '121.41.44.149',
        'port': 6432,
        'database': 'etl_data',
        'user': 'chatbot',
        'password': 'dw2We3GoMaRT4y'
    }
    
    try:
        # 连接源数据库
        source_conn = psycopg2.connect(**source_db_params)
        source_cursor = source_conn.cursor()
        
        # 连接目标数据库
        target_conn = psycopg2.connect(**target_db_params)
        target_cursor = target_conn.cursor()
        
        # 1. 获取源表中seq>=55的数据
        source_query = "SELECT * FROM ods.knowledge_catalog_v1 WHERE seq >= 55 ORDER BY seq"
        source_cursor.execute(source_query)
        source_data = source_cursor.fetchall()
        
        # 2. 获取源表和目标表的列名
        # 获取源表列名
        source_cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = 'ods' AND table_name = 'knowledge_catalog_v1' ORDER BY ordinal_position")
        source_columns = [row[0] for row in source_cursor.fetchall()]
        
        # 获取目标表列名
        target_cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = 'housing_fund' AND table_name = 'knowledge_catalog' ORDER BY ordinal_position")
        target_columns = [row[0] for row in target_cursor.fetchall()]
        
        print(f"源表列: {source_columns}")
        print(f"目标表列: {target_columns}")
        
        # 3. 准备插入数据
        # 目标表id从1开始，所以我们需要计算从1开始的序列
        start_id = 1
        
        for i, row in enumerate(source_data):
            # 创建当前行的数据字典
            source_row_dict = dict(zip(source_columns, row))
            
            # 获取当前时间
            import datetime
            current_time = datetime.datetime.now()
            
            # 构建目标表的插入数据
            target_values = []
            for col in target_columns:
                if col == 'id':
                    # id从1开始递增
                    target_values.append(start_id + i)
                elif col in source_row_dict:
                    # 如果源表有对应列，直接使用
                    target_values.append(source_row_dict[col])
                elif col == 'status':
                    # status字段不允许为空，设置默认值为1或active（根据实际业务逻辑调整）
                    target_values.append('active')  # 假设status是整数类型，1表示有效
                elif col in ['created_at', 'updated_at']:
                    # 时间字段设置为当前时间
                    target_values.append(current_time)
                else:
                    # 其他字段设置默认值
                    target_values.append(None)
            
            # 构建插入SQL
            placeholders = ', '.join(['%s'] * len(target_columns))
            insert_sql = f"INSERT INTO housing_fund.knowledge_catalog ({', '.join(target_columns)}) VALUES ({placeholders})"
            
            # 执行插入
            target_cursor.execute(insert_sql, target_values)
        
        # 提交事务
        target_conn.commit()
        
        print(f"成功插入 {len(source_data)} 条数据到 housing_fund.knowledge_catalog 表")
        
    except Exception as e:
        print(f"操作失败: {str(e)}")
        # 回滚事务
        if 'target_conn' in locals():
            target_conn.rollback()
    finally:
        # 关闭数据库连接
        if 'source_cursor' in locals():
            source_cursor.close()
        if 'source_conn' in locals():
            source_conn.close()
        if 'target_cursor' in locals():
            target_cursor.close()
        if 'target_conn' in locals():
            target_conn.close()

if __name__ == "__main__":
    import_housing_fund_catalog()
