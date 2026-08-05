import sqlite3
from pathlib import Path

from util.common import common

def get_sqlite_connection() -> sqlite3.Connection:
    config = common.config
    db_path = Path(f'{config.get('sqlite', 'sqlite_path')}')
    # 加 timeout 降低併發寫入 database is locked
    conn = sqlite3.connect(db_path, timeout=10)  # 遇到鎖住時，等待最多 10 秒再重試，而不是立刻報錯
    conn.row_factory = sqlite3.Row  # ← 讓結果可以用 column name 存取
    return conn