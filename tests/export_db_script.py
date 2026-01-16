"""
导出数据库 chatbot schema 的脚本

功能：
1. 导出表结构（DDL）- 支持 serial/bigserial 类型识别
2. 导出表数据（可选）
3. 支持选择特定的表
4. 生成完整的 SQL 导出文件

使用方式：
    # 导出所有表结构和数据
    python tests/export_db_script.py

    # 仅导出表结构
    python tests/export_db_script.py --schema-only

    # 仅导出指定的表
    python tests/export_db_script.py --tables users chats messages

    # 自定义输出文件名
    python tests/export_db_script.py --output my_backup.sql

    # 限制每个表导出的数据行数（用于测试）
    python tests/export_db_script.py --data-limit 100
"""

import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, inspect, text
from typing import Any, List, Optional
from app.config.settings import settings
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseExporter:
    """数据库导出工具类"""

    def __init__(self, db_url: str, schema_name: str = "housing_fund"):
        """
        初始化导出器

        Args:
            db_url: 数据库连接URL
            schema_name: schema名称
        """
        self.db_url = db_url
        self.schema_name = schema_name
        self.engine: Any = None
        self.inspector: Any = None

    # ================================================================
    # 数据库连接
    # ================================================================

    def connect(self):
        """连接数据库"""
        try:
            self.engine = create_engine(self.db_url)
            self.inspector = inspect(self.engine)
            logger.info(f"成功连接到数据库，schema: {self.schema_name}")
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise

    # ================================================================
    # 表操作
    # ================================================================

    def get_tables(self, table_names: Optional[List[str]] = None) -> List[str]:
        """
        获取表列表

        Args:
            table_names: 指定的表名列表，None表示获取所有表

        Returns:
            表名列表
        """
        try:
            with self.engine.connect() as conn:
                # 获取schema下的所有表
                if table_names:
                    # 过滤出存在的表
                    tables = [
                        t for t in table_names
                        if self.inspector.has_table(t, schema=self.schema_name)
                    ]
                    if len(tables) < len(table_names):
                        missing = set(table_names) - set(tables)
                        logger.warning(f"以下表不存在: {missing}")
                else:
                    tables = self.inspector.get_table_names(schema=self.schema_name)

                logger.info(f"找到 {len(tables)} 个表: {', '.join(tables)}")
                return tables

        except Exception as e:
            logger.error(f"获取表列表失败: {e}")
            raise

    # ================================================================
    # DDL 导出
    # ================================================================

    def export_schema_ddl(self, table_names: Optional[List[str]] = None) -> str:
        """
        导出schema DDL（表结构）

        Args:
            table_names: 表名列表，None表示所有表

        Returns:
            DDL SQL语句
        """
        ddl_statements = []

        # ------------------------------------------------------------
        # 添加文件头
        # ------------------------------------------------------------
        ddl_statements.append(f"-- Schema: {self.schema_name}")
        ddl_statements.append(f"-- 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        ddl_statements.append(f"--")
        ddl_statements.append(f"-- 创建Schema")
        ddl_statements.append(f"CREATE SCHEMA IF NOT EXISTS {self.schema_name};")
        ddl_statements.append(f"")

        tables = self.get_tables(table_names)

        # ------------------------------------------------------------
        # 逐个导出表结构
        # ------------------------------------------------------------
        for table_name in tables:
            try:
                ddl_statements.append(f"-- 表: {table_name}")

                # 使用 pg_catalog 获取准确的类型信息
                with self.engine.connect() as conn:
                    result = conn.execute(text("""
                        SELECT
                            a.attname AS column_name,
                            pg_catalog.format_type(a.atttypid, a.atttypmod) AS data_type,
                            CASE WHEN a.attnotnull THEN 'NOT NULL' ELSE 'NULL' END AS nullable,
                            pg_catalog.pg_get_expr(ad.adbin, ad.adrelid) AS default_value,
                            a.attnum AS position
                        FROM pg_catalog.pg_attribute a
                        LEFT JOIN pg_catalog.pg_attrdef ad
                            ON a.attrelid = ad.adrelid AND a.attnum = ad.adnum
                        WHERE a.attrelid = :table_regclass::regclass
                          AND a.attnum > 0
                          AND NOT a.attisdropped
                        ORDER BY a.attnum;
                    """), {"table_regclass": f"{self.schema_name}.{table_name}"})

                    columns = []
                    for row in result:
                        col_name = row[0]
                        data_type = row[1]
                        nullable = row[2]
                        default_val = row[3]

                        # 构建列定义
                        col_def = self._build_column_definition(
                            col_name, data_type, nullable, default_val
                        )
                        columns.append(col_def)

                    # 生成 CREATE TABLE 语句
                    ddl_statements.append(f"CREATE TABLE {self.schema_name}.{table_name} (")
                    ddl_statements.append(',\n'.join(columns))
                    ddl_statements.append(");")

                # 添加主键约束
                self._add_primary_key(ddl_statements, table_name)

                # 添加外键约束
                self._add_foreign_keys(ddl_statements, table_name)

                # 添加索引
                self._add_indexes(ddl_statements, table_name)

                ddl_statements.append("")

            except Exception as e:
                logger.error(f"导出表 {table_name} 的DDL失败: {e}")
                logger.exception(e)
                continue

        return '\n'.join(ddl_statements)

    def _build_column_definition(
        self,
        col_name: str,
        data_type: str,
        nullable: str,
        default_val: str
    ) -> str:
        """
        构建列定义

        Args:
            col_name: 列名
            data_type: 数据类型
            nullable: 是否可为空
            default_val: 默认值

        Returns:
            列定义SQL
        """
        col_def = f"    {col_name} "

        # 处理 serial 和 bigserial 类型
        # 检测: integer/bigint + nextval() => serial/bigserial
        if default_val and 'nextval' in default_val:
            if data_type in ('integer', 'int4'):
                col_def += "SERIAL"
            elif data_type in ('bigint', 'int8'):
                col_def += "BIGSERIAL"
            else:
                col_def += data_type
        else:
            col_def += data_type

        # 添加非空约束
        if 'NOT NULL' in nullable:
            col_def += " NOT NULL"

        # 添加默认值（跳过序列，因为 serial 已包含）
        if default_val and 'nextval' not in default_val:
            col_def += f" DEFAULT {default_val}"

        return col_def

    def _add_primary_key(self, ddl_statements: List[str], table_name: str):
        """添加主键约束"""
        pk = self.inspector.get_pk_constraint(table_name, schema=self.schema_name)
        if pk.get('constrained_columns'):
            ddl_statements.append(
                f"ALTER TABLE {self.schema_name}.{table_name}\n"
                f"    ADD PRIMARY KEY ({', '.join(pk['constrained_columns'])});"
            )

    def _add_foreign_keys(self, ddl_statements: List[str], table_name: str):
        """添加外键约束"""
        fks = self.inspector.get_foreign_keys(table_name, schema=self.schema_name)
        for fk in fks:
            ddl_statements.append(
                f"ALTER TABLE {self.schema_name}.{table_name}\n"
                f"    ADD CONSTRAINT {fk['name']} "
                f"FOREIGN KEY ({', '.join(fk['constrained_columns'])})\n"
                f"    REFERENCES {self.schema_name}.{fk['referred_table']} "
                f"({', '.join(fk['referred_columns'])});"
            )

    def _add_indexes(self, ddl_statements: List[str], table_name: str):
        """添加索引"""
        indexes = self.inspector.get_indexes(table_name, schema=self.schema_name)
        for idx in indexes:
            # 跳过唯一索引（已在约束中处理）
            if not idx.get('unique'):
                columns = ', '.join([str(c) for c in idx['column_names'] if c is not None])
                ddl_statements.append(
                    f"CREATE INDEX {idx['name']} "
                    f"ON {self.schema_name}.{table_name} ({columns});"
                )

    # ================================================================
    # 数据导出
    # ================================================================

    def export_table_data(self, table_name: str, limit: Optional[int] = None) -> str:
        """
        导出表数据（INSERT语句）

        Args:
            table_name: 表名
            limit: 限制导出行数，None表示全部

        Returns:
            INSERT SQL语句
        """
        try:
            with self.engine.connect() as conn:
                # 获取表的列信息
                columns = self.inspector.get_columns(table_name, schema=self.schema_name)
                column_names = [col['name'] for col in columns]

                # 构建查询
                query = f"SELECT * FROM {self.schema_name}.{table_name}"
                if limit:
                    query += f" LIMIT {limit}"

                result = conn.execute(text(query))

                insert_statements = []
                insert_statements.append(f"-- 数据: {table_name}")

                # 生成 INSERT 语句
                for row in result:
                    values = []
                    for value in row:
                        if value is None:
                            values.append("NULL")
                        elif isinstance(value, str):
                            # 转义单引号
                            escaped = value.replace("'", "''")
                            values.append(f"'{escaped}'")
                        elif isinstance(value, (dict, list)):
                            # JSON 类型
                            import json
                            escaped = json.dumps(value).replace("'", "''")
                            values.append(f"'{escaped}'")
                        else:
                            values.append(str(value))

                    insert_statements.append(
                        f"INSERT INTO {self.schema_name}.{table_name} ({', '.join(column_names)})\n"
                        f"VALUES ({', '.join(values)});"
                    )

                insert_statements.append("")
                return '\n'.join(insert_statements)

        except Exception as e:
            logger.error(f"导出表 {table_name} 的数据失败: {e}")
            return f"-- 导出表 {table_name} 的数据失败: {e}\n"

    def export_all_data(
        self,
        table_names: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> str:
        """
        导出所有表的数据

        Args:
            table_names: 表名列表，None表示所有表
            limit: 每个表限制导出行数，None表示全部

        Returns:
            INSERT SQL语句
        """
        tables = self.get_tables(table_names)
        all_data = []

        for table_name in tables:
            data = self.export_table_data(table_name, limit)
            all_data.append(data)

        return '\n'.join(all_data)

    # ================================================================
    # 完整导出
    # ================================================================

    def export_full(
        self,
        output_file: Optional[str] = None,
        schema_only: bool = False,
        tables: Optional[List[str]] = None,
        data_limit: Optional[int] = None
    ):
        """
        完整导出数据库

        Args:
            output_file: 输出文件路径
            schema_only: 是否仅导出表结构
            tables: 指定表名列表
            data_limit: 每个表限制导出行数
        """
        self.connect()

        # 生成输出文件名
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            suffix = "schema" if schema_only else "full"
            output_file = f"chatbot_{suffix}_export_{timestamp}.sql"

        logger.info(f"开始导出到文件: {output_file}")

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                # 写入文件头
                self._write_file_header(f, schema_only)

                # 导出表结构
                logger.info("导出表结构...")
                self._write_schema_ddl(f, tables)

                # 导出数据
                if not schema_only:
                    logger.info("导出表数据...")
                    self._write_table_data(f, tables, data_limit)

            # 输出成功信息
            file_size = os.path.getsize(output_file)
            size_str = self._format_file_size(file_size)
            logger.info(f"导出成功！文件已保存到: {output_file}")
            logger.info(f"文件大小: {size_str}")

        except Exception as e:
            logger.error(f"导出失败: {e}")
            raise
        finally:
            if self.engine:
                self.engine.dispose()

    def _write_file_header(self, f, schema_only: bool):
        """写入文件头"""
        f.write("-- ============================================\n")
        f.write("-- Chatbot Schema 数据库导出\n")
        f.write(f"-- Schema: {self.schema_name}\n")
        f.write(f"-- 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"-- 导出类型: {'仅表结构' if schema_only else '表结构+数据'}\n")
        f.write("-- ============================================\n\n")

    def _write_schema_ddl(self, f, tables: Optional[List[str]]):
        """写入表结构DDL"""
        f.write("-- ============================================\n")
        f.write("-- 表结构 (DDL)\n")
        f.write("-- ============================================\n\n")
        ddl = self.export_schema_ddl(tables)
        f.write(ddl)
        f.write("\n")

    def _write_table_data(self, f, tables: Optional[List[str]], limit: Optional[int]):
        """写入表数据"""
        f.write("-- ============================================\n")
        f.write("-- 表数据\n")
        f.write("-- ============================================\n\n")
        data = self.export_all_data(tables, limit)
        f.write(data)

    @staticmethod
    def _format_file_size(file_size: int) -> str:
        """格式化文件大小"""
        if file_size > 1024 * 1024:
            return f"{file_size / (1024 * 1024):.2f} MB"
        elif file_size > 1024:
            return f"{file_size / 1024:.2f} KB"
        else:
            return f"{file_size} bytes"


# ================================================================
# 命令行入口
# ================================================================

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='导出 chatbot schema 数据库',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--schema-only',
        action='store_true',
        help='仅导出表结构，不导出数据'
    )
    parser.add_argument(
        '--tables',
        nargs='+',
        metavar='TABLE',
        help='指定要导出的表名，多个表名用空格分隔'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        metavar='FILE',
        help='输出文件名（默认: chatbot_full_export_TIMESTAMP.sql）'
    )
    parser.add_argument(
        '--data-limit',
        type=int,
        metavar='N',
        help='限制每个表导出的数据行数（用于测试）'
    )

    args = parser.parse_args()

    # 创建导出器并执行导出
    try:
        exporter = DatabaseExporter(
            db_url=settings.CHAT_POSTGRES_URL,
            schema_name="housing_fund"
        )
        exporter.export_full(
            output_file=args.output,
            schema_only=args.schema_only,
            tables=args.tables,
            data_limit=args.data_limit
        )
    except Exception as e:
        logger.error(f"导出过程出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
