from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class ImageEmbedding:
    """圖片向量表資料結構，儲存圖片經由多模態模型運算出的特徵向量 (1:embedding_model_count，同 image_id + 同 model_name 僅允許 1 筆)"""

    id: Optional[int] = None
    """向量紀錄主鍵 ID (BIGINT UNSIGNED)"""

    image_id: int = 0
    """對應的主圖 ID (BIGINT UNSIGNED)，關聯 image.id"""

    model_name: str = ""
    """產生向量的模型名稱 (VARCHAR(64))，例如 "clip-vit-b32"；與 image_id 組成唯一約束"""

    vector_512: Optional[List[float]] = None
    """512 維度的浮點數特徵向量 (VECTOR(512))，用於相似度矩陣搜尋"""

    created_at: Optional[datetime] = None
    """紀錄建立時間 (DATETIME)"""

    updated_at: Optional[datetime] = None
    """紀錄最後更新時間 (DATETIME)"""