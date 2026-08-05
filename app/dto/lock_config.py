from dataclasses import dataclass


@dataclass
class LockConfig:
    """SQLite 資料表鎖的設定，供 sqlite_table_lock 裝飾器使用"""

    lock_class: str
    """鎖的類別名稱，例如 "Image_Process"，同一類別的鎖會互相搶占 max_concurrent 的名額"""

    ttl_seconds: int = 60
    """鎖的存活時間 (Time To Live)，單位秒；超過這個時間鎖會視為過期，避免程式當機造成死鎖"""

    retry_interval: float = 1.0
    """沒搶到鎖時，隔多少秒重試一次"""

    timeout: int = 10
    """最大排隊等待時間，單位秒；超過這個時間仍未搶到鎖，會拋出 TimeoutError"""

    max_concurrent: int = 1
    """允許同時處理的最大 session 數，達到上限前的請求都能拿到鎖"""