from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ImageTransform:
    """風格轉換流水表資料結構，記錄原始圖片經由生成式模型轉換後的衍生圖片路徑與參數 (1:N)"""

    id: Optional[int] = None
    """轉換流水紀錄主鍵 ID (BIGINT UNSIGNED)"""

    image_id: int = 0
    """對應的原圖 ID (BIGINT UNSIGNED)，關聯 image.id"""

    transform_model: str = ""
    """執行的風格轉換模型名稱 (VARCHAR(64))，例如 "sd-image-variations-v2" """

    transform_path: Path | str = ""
    """風格轉換後生成的新圖片路徑 (VARCHAR(512))，支援 pathlib.Path 或字串"""

    created_at: Optional[datetime] = None
    """紀錄建立時間 (DATETIME)"""

    updated_at: Optional[datetime] = None
    """紀錄最後更新時間 (DATETIME)"""