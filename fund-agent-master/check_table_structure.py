#!/usr/bin/env python3
# 查询indexed_knowledge表结构

from app.config.database import SessionLocal, global_schema
from sqlalchemy import text

with SessionLocal() as session:
    result = session.execute(
        text('SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = :schema AND table_name = :table'),
        {'schema': global_schema, 'table': 'indexed_knowledge'}
    )
    rows = result.fetchall()
    print('indexed_knowledge表结构:')
    print('-' * 50)
    for row in rows:
        print(f'{row[0]:<30} {row[1]}')
    print('-' * 50)