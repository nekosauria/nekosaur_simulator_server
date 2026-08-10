from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from util.common import common


@dataclass
class ImageDetection:
    """物件偵測流水表資料結構，記錄特定圖片經由物件偵測模型處理後的結果 (1:detect_model_count，同 image_id + 同 detect_model 僅允許 1 筆)"""

    id: Optional[int] = None
    """偵測流水紀錄主鍵 ID (BIGINT UNSIGNED)"""

    image_id: int = 0
    """對應的主圖 ID (BIGINT UNSIGNED)，關聯 image.id"""

    md5_hash: str = ""
    """此標註框圖自身的 MD5 雜湊值 (CHAR(32))，具有唯一性約束，用於避免重複圖檔寫入"""

    detect_path: Path = ""
    """渲染繪製標註框後的圖片儲存路徑 (VARCHAR(512))，支援 pathlib.Path 或字串"""

    detect_model: str = ""
    """執行的偵測模型名稱 (VARCHAR(64))，例如 "yolov8n", "yolov11x" """

    has_cat: bool = False
    """該次偵測是否偵測到貓 (BOOLEAN)"""

    is_preprocessed: bool = False
    """是否為預處理(非使用者當下觸發)產生的偵測結果 (BOOLEAN)"""

    predict_list: Optional[Dict[str, Any]] = None
    """模型偵測結果的原始 JSON 數據 (JSON)，例如各類別的信心分數與邊界框座標"""

    tag_results: Optional[Dict[str, Any]] = None
    """前端或繪圖組件使用的可畫圖標記資訊 (JSON)"""

    created_at: Optional[datetime] = None
    """紀錄建立時間 (DATETIME)"""

    updated_at: Optional[datetime] = None
    """紀錄最後更新時間 (DATETIME)"""

    def __post_init__(self):
        # 只要傳進來的是 str，自動幫忙轉成 Path 物件
        self.detect_path = common.to_path(self.detect_path)
        self.has_cat = bool(self.has_cat)
        self.is_preprocessed = bool(self.is_preprocessed)