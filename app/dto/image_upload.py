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

    # --- Origin Detector 偵測結果 ---
    origin_image_path: str
    """原圖對外可存取網址。"""

    origin_detect_path: str
    """原圖偵測結果圖（含 draw box 標註）的對外可存取網址。"""

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

    # --- Similar Detector 偵測結果 ---
    similar_image_path: str
    """相似圖片對外可存取網址。"""

    similar_detect_path: str
    """相似圖片偵測結果圖對外可存取網址。"""

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

    origin_transform_model: str
    """原圖風格轉換所使用的模型名稱。"""

    origin_transform_is_preprocessed: bool
    """原圖轉換結果是否為預處理快取。"""

    origin_transform_created_at: str
    """原圖轉換紀錄的建立時間（"%Y-%m-%d %H:%M:%S" 格式字串，伺服器本地時間）。"""

    # --- Similar Transform 風格轉換結果 ---
    similar_transform_path: str
    """相似圖風格轉換後的結果圖對外可存取網址。"""

    similar_transform_model: str
    """相似圖風格轉換所使用的模型名稱。"""

    similar_transform_is_preprocessed: bool
    """相似圖轉換結果是否為預處理快取。"""

    similar_transform_created_at: str
    """相似圖轉換紀錄的建立時間（"%Y-%m-%d %H:%M:%S" 格式字串，伺服器本地時間）。"""

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
        "origin_detect_created_at",
        "similar_similar_created_at",
        "origin_transform_created_at",
        "similar_transform_created_at",
    )

    def __post_init__(self):
        """
        統一將四個 created_at 欄位正規化為 "%Y-%m-%d %H:%M:%S" 字串。

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
            # http stat
            "success": self.success,
            # 偵測結果
            "detector": {
                # origin
                "origin": {
                    "image": self.origin_image_path,
                    "detect_image": self.origin_detect_path,
                    "detect_model": self.origin_detect_model,
                    "has_neko": self.origin_has_cat,
                    "is_cache": self.origin_detect_is_preprocessed,
                    "score_list": self.origin_predict_list,
                    "score_results": self.origin_tag_results,
                    "create_time": self.origin_detect_created_at,
                },
                # similar
                "similar": {
                    "image": self.similar_image_path,
                    "detect_image": self.similar_detect_path,
                    "detect_model": self.similar_detect_model,
                    "has_neko": self.similar_has_cat,
                    "is_cache": self.similar_is_preprocessed,
                    "score_list": self.similar_predict_list,
                    "score_results": self.similar_tag_results,
                    "create_time": self.similar_similar_created_at,
                },
            },
            # 風格轉換結果
            "transform": {
                # origin
                "origin": {
                    "transform_image": self.origin_transform_path,
                    "transform_model": self.origin_transform_model,
                    "is_cache": self.origin_transform_is_preprocessed,
                    "create_time": self.origin_transform_created_at,
                },
                # similar
                "similar": {
                    "transform_image": self.similar_transform_path,
                    "transform_model": self.similar_transform_model,
                    "is_cache": self.similar_transform_is_preprocessed,
                    "create_time": self.similar_transform_created_at,
                },
            },
            # metrics
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