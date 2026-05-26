import functools
import sqlite3
import time
from util.sqlite import get_db


def sqlite_table_lock(lock_class, ttl_seconds=60, retry_interval=1.0, timeout=10, max_concurrent=1):
    """
    基於 SQLite 資料表的分散式鎖裝飾器
    :param lock_class:     鎖的類別名稱 (字串)
    :param ttl_seconds:    鎖的存活時間 (TTL)，防止當機死鎖
    :param retry_interval: 沒搶到鎖時，隔多少秒重試一次
    :param timeout:        最大排隊等待時間，超過則拋出逾時異常
    :param max_concurrent: 允許同時處理的最大 session 數
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            row_id = _acquire_lock(lock_class, ttl_seconds, retry_interval, timeout, max_concurrent)
            try:
                return func(*args, **kwargs)
            finally:
                _release_lock(row_id)

        return wrapper
    return decorator


def _acquire_lock(lock_class, ttl_seconds, retry_interval, timeout, max_concurrent):
    """
    搶鎖邏輯：在 timeout 內不斷重試
    成功條件：active session 數 < max_concurrent
    回傳：成功 insert 的 row id，釋放鎖時用
    """
    start_time = time.time()
    print(f"[⏳ LOCK TRY] 嘗試獲取資料庫鎖 [{lock_class}]...")

    while time.time() - start_time < timeout:
        current_now = int(time.time())
        expire_time = current_now + ttl_seconds

        db = get_db()
        try:
            with db:
                # 查目前 active session 數（未完成且未過期）
                row = db.execute("""
                    SELECT COUNT(*) FROM sys_state
                    WHERE lock_class = ?
                      AND is_locked = 1
                      AND timestamp > ?
                """, (lock_class, current_now)).fetchone()

                active_count = row[0]

                if active_count < max_concurrent:
                    cursor = db.execute("""
                        INSERT INTO sys_state (lock_class, timestamp, is_locked, created_at)
                        VALUES (?, ?, 1, datetime('now'))
                    """, (lock_class, expire_time))
                    row_id = cursor.lastrowid
                    print(
                        f"[🔑 LOCK ACQUIRED] 成功取得鎖 [{lock_class}]，id={row_id}，active={active_count + 1}/{max_concurrent}")
                    return row_id

        except sqlite3.Error as e:
            print(f"[❌ DB Error] {e}")
        finally:
            db.close()

        time.sleep(retry_interval)  # 沒搶到，等一下再重試

    raise TimeoutError(f"搶鎖逾時！無法取得 [{lock_class}] 的控制權。")


def _release_lock(row_id):
    """ 釋放鎖：更新指定 id 那筆，標記完成時間 """
    db = get_db()
    try:
        with db:
            db.execute("""
                UPDATE sys_state
                SET is_locked = 0,
                    finished_at = datetime('now')
                WHERE id = ?
            """, (row_id,))
        print(f"[🔓 LOCK RELEASED] 已釋放鎖 id={row_id}\n")
    except sqlite3.Error as e:
        print(f"[❌ RELEASE Error] {e}")
    finally:
        db.close()