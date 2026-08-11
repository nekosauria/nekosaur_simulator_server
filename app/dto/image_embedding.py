from dataclasses import dataclass

from PIL import Image


@dataclass
class EmbeddingRequest:
    """
    向量相似圖搜尋服務的輸入資料結構。
    """

    req_image: Image.Image | None
    """欲編碼的圖片物件，若為 None 代表僅需文字編碼。"""

    embedding_model: str
    """使用的 embedding 模型名稱（對應 ImageConst 常數）。"""


@dataclass
class EmbeddingResult:
    """
    向量相似圖搜尋服務的輸出資料結構。
    """

    image_embedding_vector: list[float]
    """
    圖片編碼後的向量結果，維度需與 MariaDB image_embedding 表 VECTOR(512) 欄位一致。
    須為 JSON 可序列化的 list，供 DAO 層 json.dumps() 後寫入 VEC_FromText()。
    """