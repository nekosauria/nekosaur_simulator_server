from dataclasses import dataclass
from datetime import datetime


@dataclass
class ImageUploadResponse:
    """
    /upload 端點對外回傳的 response schema。
    集中管理 API 回傳格式，避免 controller 內直接組 dict 導致欄位名稱漂移不受型別檢查保護。
    """

    success: bool
    """
    本次上傳處理是否成功。失敗情況應由 controller 的例外處理直接回傳錯誤 response，
    此欄位為 True 時代表偵測、向量搜尋、風格轉換三個步驟皆已完整執行。
    """

    # --- Origin Image ---
    origin_image_path: str
    """原圖對外可存取網址。"""

    origin_image_md5_hash: str
    """原圖 (image 表) 的 md5。"""

    origin_image_created_at: str
    """原圖 (image 表) 紀錄的建立時間（"%Y-%m-%d %H:%M:%S" 格式字串，伺服器本地時間）。"""

    # --- Origin Detector 偵測結果 ---
    origin_detect_path: str
    """原圖偵測結果圖（含 draw box 標註）的對外可存取網址。"""

    origin_detect_md5_hash: str
    """原圖偵測結果圖自身的 md5。"""

    origin_detect_model: str
    """原圖偵測所使用的模型名稱。"""

    origin_has_cat: bool
    """原圖是否偵測到貓。"""

    origin_detect_is_preprocessed: bool
    """原圖偵測結果是否為預處理快取。"""

    origin_predict_list: dict
    """原圖完整的模型預測結果列表。"""

    origin_tag_results: dict
    """原圖各標籤的信心分數彙總。"""

    origin_detect_created_at: str
    """原圖偵測紀錄的建立時間（"%Y-%m-%d %H:%M:%S" 格式字串，伺服器本地時間）。"""

    # --- Similar Image ---
    similar_image_path: str
    """相似圖片對外可存取網址。"""

    similar_image_md5_hash: str
    """相似圖 (image 表) 的 md5。"""

    similar_image_created_at: str
    """相似圖 (image 表) 紀錄的建立時間（"%Y-%m-%d %H:%M:%S" 格式字串，伺服器本地時間）。"""

    similar_distance: float
    """Vector Search 的 Cosine Distance (0.0 ~ 2.0)
    數值越小代表向量越相似 (Similarity = 1 - Distance)

    常見距離門檻判讀：
    - 0.00 ~ 0.15: 非常相似 (幾乎同圖/輕微變形)
    - 0.15 ~ 0.25: 相當相似 (同主題/同類型物件)
    - 0.25 ~ 0.30: 邊緣相關 (僅背景或構圖部分相似)
    - > 0.30     : 差異極大 (視覺上不太像)
    """

    similar_distance_percent:float
    """轉換成人類易讀的百分比"""

    # --- Similar Detector 偵測結果 ---
    similar_detect_path: str
    """相似圖片偵測結果圖對外可存取網址。"""

    similar_detect_md5_hash: str
    """相似圖偵測結果圖自身的 md5。"""

    similar_detect_model: str
    """相似圖片偵測所使用的模型名稱。"""

    similar_has_cat: bool
    """相似圖片是否偵測到貓。"""

    similar_is_preprocessed: bool
    """相似圖片偵測結果是否為預處理快取。"""

    similar_predict_list: dict
    """相似圖片完整的模型預測結果列表。"""

    similar_tag_results: dict
    """相似圖片各標籤的信心分數彙總。"""

    similar_similar_created_at: str
    """相似圖片紀錄的建立時間（"%Y-%m-%d %H:%M:%S" 格式字串，伺服器本地時間）。"""

    # --- Origin Transform 風格轉換結果 ---
    origin_transform_path: str
    """原圖風格轉換後的結果圖對外可存取網址。"""

    origin_transform_md5_hash: str
    """原圖轉換結果圖自身的 md5。"""

    origin_transform_model: str
    """原圖風格轉換所使用的模型名稱。"""

    origin_transform_is_preprocessed: bool
    """原圖轉換結果是否為預處理快取。"""

    origin_transform_created_at: str
    """原圖轉換紀錄的建立時間（"%Y-%m-%d %H:%M:%S" 格式字串，伺服器本地時間）。"""

    # --- Similar Transform 風格轉換結果 ---
    similar_transform_path: str
    """相似圖風格轉換後的結果圖對外可存取網址。"""

    similar_transform_md5_hash: str
    """相似圖轉換結果圖自身的 md5。"""

    similar_transform_model: str
    """相似圖風格轉換所使用的模型名稱。"""

    similar_transform_is_preprocessed: bool
    """相似圖轉換結果是否為預處理快取。"""

    similar_transform_created_at: str
    """相似圖轉換紀錄的建立時間（"%Y-%m-%d %H:%M:%S" 格式字串，伺服器本地時間）。"""

    # --- Origin Embedding 向量結果 ---
    origin_embedding_model: str
    """原圖向量抽取所使用的模型名稱。"""

    origin_embedding_vector_512: list[float]
    """原圖的 CLIP 512 維向量。"""

    origin_embedding_created_at: str
    """原圖向量紀錄的建立時間（"%Y-%m-%d %H:%M:%S" 格式字串，伺服器本地時間）。"""

    # --- Similar Embedding 向量結果 ---
    similar_embedding_model: str
    """相似圖向量抽取所使用的模型名稱。"""

    similar_embedding_vector_512: list[float]
    """相似圖的 CLIP 512 維向量。"""

    similar_embedding_created_at: str
    """相似圖向量紀錄的建立時間（"%Y-%m-%d %H:%M:%S" 格式字串，伺服器本地時間）。"""

    # --- Metrics & System ---
    image_process_count: int
    """目前累計的圖片處理次數。"""

    image_validate_cost: float
    """圖片驗證與前處理耗費的時間（秒）。"""

    image_embedding_cost: float
    """圖片向量特徵抽取與搜尋耗費的時間（秒）。"""

    origin_detector_cost: float
    """原圖偵測步驟耗費的時間（秒）。"""

    similar_detector_cost: float
    """相似圖片搜尋與處理耗費的時間（秒）。"""

    origin_transform_cost: float
    """原圖風格轉換耗費的時間（秒）。"""

    similar_transform_cost: float
    """相似圖風格轉換耗費的時間（秒）。"""

    api_cost: float
    """本次 API 請求總耗費時間（秒）。"""

    # 需要統一轉換成字串的建立時間欄位名稱
    _DATETIME_FIELDS = (
        "origin_image_created_at",
        "similar_image_created_at",
        "origin_detect_created_at",
        "similar_similar_created_at",
        "origin_transform_created_at",
        "similar_transform_created_at",
        "origin_embedding_created_at",
        "similar_embedding_created_at",
    )

    def __post_init__(self):
        """
        統一將八個 created_at 欄位正規化為 "%Y-%m-%d %H:%M:%S" 字串。

        上游 entity 的 created_at 屬性可能是 datetime 物件（DAO 讀出來未轉換）
        也可能已經是字串，這裡統一收斂成同一種格式，避免不同路徑序列化結果不一致，
        導致 Flask jsonify() 對 naive datetime 物件自動轉成 RFC 1123 格式
        （例如 "Tue, 11 Aug 2026 11:42:28 GMT"）造成前端解析錯誤。

        注意：這裡不做時區轉換，純粹格式化，因為系統資料庫存的本來就是伺服器本地時間
        （DATETIME + CURRENT_TIMESTAMP，未設定 UTC time_zone）。
        """
        for field_name in self._DATETIME_FIELDS:
            value = getattr(self, field_name)
            if isinstance(value, datetime):
                setattr(self, field_name, value.strftime("%Y-%m-%d %H:%M:%S"))
            elif value is not None and not isinstance(value, str):
                # 非預期型別，明確拋錯而非靜默吞掉，符合「拒絕預設值、寧可失敗要吵」的原則
                raise TypeError(
                    f"{field_name} 預期為 datetime 或 str，實際收到 {type(value).__name__}: {value!r}"
                )

    def to_dict(self) -> dict:
        """將 response 物件序列化為 dict，供 Flask jsonify() 使用。"""
        return {
            "success": self.success,
            "origin": {
                "image": {
                    "image_path": self.origin_image_path,
                    "md5_hash": self.origin_image_md5_hash,
                    "created_at": self.origin_image_created_at,
                },
                "detector": {
                    "detect_path": self.origin_detect_path,
                    "md5_hash": self.origin_detect_md5_hash,
                    "detect_model": self.origin_detect_model,
                    "has_cat": self.origin_has_cat,
                    "is_preprocessed": self.origin_detect_is_preprocessed,
                    "predict_list": self.origin_predict_list,
                    "tag_results": self.origin_tag_results,
                    "created_at": self.origin_detect_created_at,
                },
                "transform": {
                    "transform_path": self.origin_transform_path,
                    "md5_hash": self.origin_transform_md5_hash,
                    "transform_model": self.origin_transform_model,
                    "is_preprocessed": self.origin_transform_is_preprocessed,
                    "created_at": self.origin_transform_created_at,
                },
                "embedding": {
                    "embedding_model": self.origin_embedding_model,
                    "vector_512": self.origin_embedding_vector_512,
                    "created_at": self.origin_embedding_created_at,
                },
            },
            "similar": {
                "image": {
                    "image": self.similar_image_path,
                    "md5_hash": self.similar_image_md5_hash,
                    "created_at": self.similar_image_created_at,
                    "distance": self.similar_distance,
                    # 人類易讀的百分比
                    "distance_percent": self.similar_distance_percent,
                },
                "detector": {
                    "detect_path": self.similar_detect_path,
                    "md5_hash": self.similar_detect_md5_hash,
                    "detect_model": self.similar_detect_model,
                    "has_cat": self.similar_has_cat,
                    "is_preprocessed": self.similar_is_preprocessed,
                    "predict_list": self.similar_predict_list,
                    "tag_results": self.similar_tag_results,
                    "created_at": self.similar_similar_created_at,
                },
                "transform": {
                    "transform_path": self.similar_transform_path,
                    "md5_hash": self.similar_transform_md5_hash,
                    "transform_model": self.similar_transform_model,
                    "is_preprocessed": self.similar_transform_is_preprocessed,
                    "created_at": self.similar_transform_created_at,
                },
                "embedding": {
                    "embedding_model": self.similar_embedding_model,
                    "vector_512": self.similar_embedding_vector_512,
                    "created_at": self.similar_embedding_created_at,
                },
            },
            "metrics": {
                "image_process_count": self.image_process_count,
                "image_validate_cost": self.image_validate_cost,
                "image_embedding_cost": self.image_embedding_cost,
                "origin_detector_cost": self.origin_detector_cost,
                "similar_detector_cost": self.similar_detector_cost,
                "origin_transform_cost": self.origin_transform_cost,
                "similar_transform_cost": self.similar_transform_cost,
                "api_cost": self.api_cost,
            },
        }