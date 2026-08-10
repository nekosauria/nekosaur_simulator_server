from dataclasses import dataclass
from pathlib import Path


@dataclass
class EmbeddingRequest:
    """
    向量相似圖搜尋服務的輸入資料結構。
    """

    image_id: int
    """
    原圖在 image 表的主鍵 id，向量搜尋時排除自身，並用於關聯 image_embedding 紀錄。
    """

    origin_path: Path
    """
    原圖的實際存檔路徑，若尚未有現成 embedding，服務可依此路徑重新產生向量。
    """

