import sqlite3
from contextlib import contextmanager
from pathlib import Path

from util.common import common


def get_sqlite_connection() -> sqlite3.Connection:
    config = common.config
    db_path = Path(f'{config.get("sqlite", "sqlite_path")}')
    # 加 timeout 降低併發寫入 database is locked
    conn = sqlite3.connect(db_path, timeout=10)  # 遇到鎖住時，等待最多 10 秒再重試，而不是立刻報錯
    conn.row_factory = sqlite3.Row  # ← 讓結果可以用 column name 存取
    return conn


@contextmanager
def sqlite_connection():
    """
    真正會 close 連線的 context manager。
    sqlite3.Connection 原生的 __exit__ 只會 commit/rollback，不會 close，
    直接用 `with get_sqlite_connection()` 會導致連線持續累積、不釋放。
    這裡用 try/finally 確保無論成功或例外都會關閉連線。
    """
    conn = get_sqlite_connection()
    try:
        yield conn
    finally:
        conn.close()