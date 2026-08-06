import threading
import time

from entity.sys_state import SysState as SysStateEntity
from util.common import common
from util.sqlite import sqlite_connection

config = common.config


class SysState:
    """適合高頻率呼叫 (High Throughput) 的 DAO / Repository"""

    def __init__(self):
        self._cache = {}
        self._ttl_cache = int(config.get('lock', 'ttl_cache'))  # 快取存活時間
        self._lock = threading.Lock()

    def get_count(self, sys_state: SysStateEntity) -> int:
        if not sys_state or getattr(sys_state, "lock_class", None) is None:
            return 0

        now = time.time()
        key = sys_state.lock_class

        with self._lock:
            # 1. 記憶體快取 (Cache Layer) - 1 秒內有查詢過直接秒回，完全不用觸發 DB
            if key in self._cache:
                cached_count, timestamp = self._cache[key]
                if now - timestamp < self._ttl_cache:
                    return cached_count

            # 2. 快取過期，開啟連線查詢，查完立刻 close()
            with sqlite_connection() as db:
                cursor = db.execute(
                    """
                    SELECT COUNT(*) FROM sys_state
                    WHERE lock_class = ?
                    """,
                    (key,),
                )
                row = cursor.fetchone()
                count = row[0] if row else 0

            # 3. 更新快取
            self._cache[key] = (count, now)
            return count


# 建立單例物件 (Singleton Instance)，全域共享快取與 DB 連線
sys_state_dao = SysState()