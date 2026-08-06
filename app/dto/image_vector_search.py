from dataclasses import dataclass
from pathlib import Path


@dataclass
class VectorSearchRequest:
    """
    向量相似圖搜尋服務的輸入資料結構。
    """

    image_id: int
    """
    原圖在 image 表的主鍵 id，向量搜尋時排除自身，並用於關聯 image_embedding 紀錄。
    """

    ora_path: Path
    """
    原圖的實際存檔路徑，若尚未有現成 embedding，服務可依此路徑重新產生向量。
    """


@dataclass
class VectorSearchResult:
    """
    向量相似圖搜尋服務的輸出結果，供 controller 組裝 API response 或傳遞給後續風格轉換服務使用。
    """

    similar_path: Path
    """
    向量搜尋比對出的最相似圖片存檔路徑。
    """

    vector_search_cost: float
    """
    本次向量相似圖搜尋耗費的時間，單位為秒，已四捨五入至小數點後 3 位。
    """