from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from util.common import common


@dataclass
class Image:
    """圖片主表資料結構，儲存原始圖片的實體檔案與基本資訊"""

    id: Optional[int] = None
    """圖片主鍵 ID (BIGINT UNSIGNED)"""

    md5_hash: str = ""
    """圖片檔案的 MD5 雜湊值 (CHAR(32))，具有唯一性約束，用於避免重複圖檔寫入"""

    origin_path: Path = ""
    """原始圖片在伺服器或儲存庫中的路徑 (VARCHAR(512))，支援 pathlib.Path 或字串"""

    image_source: Optional[str] = None
    """圖片來源網址或原始標記 (VARCHAR(512))"""

    raw_source: Optional[Dict[str, Any] | List[Any] | str] = None
    """第三方 API 回傳的原始 JSON 備查 or 使用者上傳圖片內容 (JSON)"""

    is_deleted: bool = False
    """軟刪除標記 (BOOLEAN)；False 表示正常，True 表示已刪除"""

    deleted_at: Optional[datetime] = None
    """軟刪除時間 (DATETIME)；未刪除時為 None"""

    last_checked_at: Optional[datetime] = None
    """health daemon 上次檢查（存在性/有無貓，連同關聯 detection/transform）的時間 (DATETIME)"""

    created_at: Optional[datetime] = None
    """紀錄建立時間 (DATETIME)"""

    updated_at: Optional[datetime] = None
    """紀錄最後更新時間 (DATETIME)"""

    def __post_init__(self):
        # 只要傳進來的是 str，自動幫忙轉成 Path 物件
        self.origin_path = common.to_path(self.origin_path)

        # 強制將 DB 帶出的 0/1 或 int 轉為真正的 Python bool
        self.is_deleted = bool(self.is_deleted)