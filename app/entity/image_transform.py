from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
from util.common import common

@dataclass
class ImageTransform:
    """風格轉換流水表資料結構，記錄原始圖片經由生成式模型轉換後的衍生圖片路徑與參數 (1:N，同 image_id + 同 transform_model + 同 style_ref_path 可多筆)"""

    id: Optional[int] = None
    """轉換流水紀錄主鍵 ID (BIGINT UNSIGNED)"""

    image_id: int = 0
    """對應的原圖 ID (BIGINT UNSIGNED)，關聯 image.id"""

    md5_hash: str = ""
    """此轉換後圖片自身的 MD5 雜湊值 (CHAR(32))，用於避免重複圖檔寫入"""

    transform_path: Path = ""
    """風格轉換後生成的新圖片路徑 (VARCHAR(512))，支援 pathlib.Path 或字串"""

    transform_model: str = ""
    """執行的風格轉換模型名稱 (VARCHAR(64))，例如 "sd-image-variations-v2" """

    style_ref_path: Path = ""
    """使用的風格參考圖路徑 (VARCHAR(255))，支援 pathlib.Path 或字串，例如 "static/images/style/dinosaur.png" """

    is_use: bool = False
    """此快取是否已被使用過 (BOOLEAN)"""

    is_preprocessed: bool = False
    """是否為預處理(非使用者當下觸發)產生的偵測結果 (BOOLEAN)"""

    created_at: Optional[datetime] = None
    """紀錄建立時間 (DATETIME)"""

    updated_at: Optional[datetime] = None
    """紀錄最後更新時間 (DATETIME)"""

    def __post_init__(self):
        self.transform_path = common.to_path(self.transform_path)
        self.style_ref_path = common.to_path(self.style_ref_path)
        self.is_use = bool(self.is_use)
        self.is_preprocessed = bool(self.is_preprocessed)