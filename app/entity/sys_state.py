from dataclasses import dataclass
from typing import Optional


@dataclass
class SysState:
    """系統狀態與並發鎖紀錄，對應 SQLite 的系統狀態資料表"""

    lock_class: str
    """鎖的類別名稱 (TEXT)，例如 "Image_Process"，用於分類與搶佔排隊名額"""

    id: Optional[int] = None
    """鎖紀錄主鍵 ID (INTEGER PRIMARY KEY)"""

    expire_at: Optional[int] = None
    """鎖的過期時間戳記 (INTEGER)，使用 Unix Timestamp（秒）；超過此時間視為釋放"""

    is_locked: int = 1
    """目前鎖定狀態 (INTEGER)；1 表示處理中，0 表示已完成/釋放"""

    created_at: Optional[str] = None
    """紀錄建立時間 (TEXT)，格式為 UTC 時間字串，由 SQLite 的 datetime('now') 自動產生"""

    finished_at: Optional[str] = None
    """任務完成或釋放鎖的時間 (TEXT)，未完成時為 None"""