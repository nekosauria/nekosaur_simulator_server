from util.sqlite import get_db

def count_records(lock_class):
    db = get_db()
    try:
        row = db.execute("""
            SELECT COUNT(*) FROM sys_state
            WHERE lock_class = ?
        """, (lock_class,)).fetchone()
        return row[0]
    finally:
        db.close()