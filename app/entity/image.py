from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Image:
    """圖片主表資料結構，儲存原始圖片的實體檔案與基本資訊"""

    id: Optional[int] = None
    """圖片主鍵 ID (BIGINT UNSIGNED)"""

    md5_hash: str = ""
    """圖片檔案的 MD5 雜湊值 (CHAR(32))，具有唯一性約束，用於避免重複圖檔寫入"""

    origin_path: Path | str = ""
    """原始圖片在伺服器或儲存庫中的路徑 (VARCHAR(512))，支援 pathlib.Path 或字串"""

    image_source: Optional[str] = None
    """圖片來源網址或原始標記 (VARCHAR(512))"""

    raw_source: Optional[Dict[str, Any] | List[Any] | str] = None
    """第三方 API 回傳的原始 JSON 備查 or 使用者上傳圖片內容 (JSON)"""

    is_deleted: int = 0
    """軟刪除標記 (TINYINT(1))；0 表示正常，1 表示已刪除"""

    deleted_at: Optional[datetime] = None
    """軟刪除時間 (DATETIME)；未刪除時為 None"""

    created_at: Optional[datetime] = None
    """紀錄建立時間 (DATETIME)"""

    updated_at: Optional[datetime] = None
    """紀錄最後更新時間 (DATETIME)"""