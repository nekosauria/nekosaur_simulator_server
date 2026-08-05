from entity.sys_state import SysState
from util.sqlite import get_sqlite_connection


def get_count(state: SysState) -> int:
    db = get_sqlite_connection()
    try:
        row = db.execute("""
            SELECT COUNT(*) FROM sys_state
            WHERE lock_class = ?
        """, (state.lock_class,)).fetchone()
        return row[0]
    finally:
        db.close()