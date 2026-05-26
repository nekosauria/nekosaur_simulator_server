import sqlite3
from util.common import common

def get_db():
    config = common.config
    db_path = config.get('database', 'sqlite_path')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # ← 讓結果可以用 column name 存取
    return conn