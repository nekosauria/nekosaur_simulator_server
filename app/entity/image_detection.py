from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ImageDetection:
    """物件偵測流水表資料結構，記錄特定圖片經由物件偵測模型處理後的結果 (1:N)"""

    id: Optional[int] = None
    """偵測流水紀錄主鍵 ID (BIGINT UNSIGNED)"""

    image_id: int = 0
    """對應的主圖 ID (BIGINT UNSIGNED)，關聯 image.id"""

    detect_model: str = ""
    """執行的偵測模型名稱 (VARCHAR(64))，例如 "yolov8n", "yolov11x" """

    detect_path: Optional[Path | str] = None
    """渲染繪製標註框後的圖片儲存路徑 (VARCHAR(512))，支援 pathlib.Path 或字串"""

    predict_list: Optional[Dict[str, Any]] = None
    """模型偵測結果的原始 JSON 數據 (JSON)，例如各類別的信心分數與邊界框座標"""

    tag_results: Optional[Dict[str, Any]] = None
    """前端或繪圖組件使用的可畫圖標記資訊 (JSON)"""

    created_at: Optional[datetime] = None
    """紀錄建立時間 (DATETIME)"""

    updated_at: Optional[datetime] = None
    """紀錄最後更新時間 (DATETIME)"""