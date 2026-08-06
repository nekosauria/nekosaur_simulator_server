import functools
import sqlite3
import time

from dto.lock_config import LockConfig
from entity.sys_state import SysState
from util.common import common
from util.sqlite import get_sqlite_connection, sqlite_connection

logger = common.logger


def sqlite_table_lock(config: LockConfig):
    """
    基於 SQLite 資料表的分散式鎖裝飾器
    :param config: 鎖的設定（lock_class、ttl_seconds、retry_interval、timeout、max_concurrent）
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            lock_state = _acquire_lock(config)
            try:
                return func(*args, **kwargs)
            finally:
                _release_lock(lock_state)

        return wrapper
    return decorator


def _acquire_lock(config: LockConfig) -> SysState:
    """
    搶鎖邏輯：在 timeout 內不斷重試
    成功條件：active session 數 < max_concurrent
    回傳：成功寫入的 SysState（含 db 產生的 id），釋放鎖時用
    """
    start_time = time.time()
    logger.debug(f"[⏳ LOCK TRY] 嘗試獲取 [{config.lock_class}] 資料庫鎖 ...")

    while time.time() - start_time < config.timeout:
        current_now = int(time.time())
        expire_time = current_now + config.ttl_seconds

        try:
            # with allow automatic connection close
            with sqlite_connection() as db:
                # with allow automatic commit
                with db:
                    row = db.execute("""
                        SELECT COUNT(*) FROM sys_state
                        WHERE lock_class = ?
                          AND is_locked = 1
                          AND expire_at > ?
                    """, (config.lock_class, current_now)).fetchone()

                    active_count = row[0]

                    if active_count < config.max_concurrent:
                        lock_state = SysState(
                            lock_class=config.lock_class,
                            expire_at=expire_time,
                            is_locked=1,
                        )

                        cursor = db.execute("""
                            INSERT INTO sys_state (lock_class, expire_at, is_locked, created_at)
                            VALUES (?, ?, ?, datetime('now'))
                        """, (lock_state.lock_class, lock_state.expire_at, lock_state.is_locked))

                        lock_state.id = cursor.lastrowid

                        logger.debug(
                            f"[🔑 LOCK ACQUIRED] 成功取得鎖 [{config.lock_class}]，id={lock_state.id}，active={active_count + 1}/{config.max_concurrent}")
                        return lock_state

        except sqlite3.Error as e:
            logger.error(f"[❌ DB Error] {e}")

        time.sleep(config.retry_interval)  # 沒搶到，等一下再重試

    raise TimeoutError(f"搶鎖逾時！無法取得 [{config.lock_class}] 的控制權。")


def _release_lock(lock_state: SysState):
    """ 釋放鎖：更新指定 id 那筆，標記完成時間 """
    try:
        with sqlite_connection() as db:
            with db:
                db.execute("""
                    UPDATE sys_state
                    SET is_locked = 0,
                        finished_at = datetime('now')
                    WHERE id = ?
                """, (lock_state.id,))
        logger.debug(f"[🔓 LOCK RELEASED] 已釋放鎖 id={lock_state.id}\n")
    except sqlite3.Error as e:
        logger.error(f"[❌ RELEASE Error] {e}")