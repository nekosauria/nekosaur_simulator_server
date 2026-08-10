from dataclasses import dataclass


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
    """原圖偵測紀錄的建立時間（ISO 格式字串）。"""

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
    """相似圖片紀錄的建立時間（ISO 格式字串）。"""

    # --- Origin Transform 風格轉換結果 ---
    origin_transform_path: str
    """原圖風格轉換後的結果圖對外可存取網址。"""

    origin_transform_model: str
    """原圖風格轉換所使用的模型名稱。"""

    origin_transform_is_preprocessed: bool
    """原圖轉換結果是否為預處理快取。"""

    origin_transform_created_at: str
    """原圖轉換紀錄的建立時間（ISO 格式字串）。"""

    # --- Similar Transform 風格轉換結果 ---
    similar_transform_path: str
    """相似圖風格轉換後的結果圖對外可存取網址。"""

    similar_transform_model: str
    """相似圖風格轉換所使用的模型名稱。"""

    similar_transform_is_preprocessed: bool
    """相似圖轉換結果是否為預處理快取。"""

    similar_transform_created_at: str
    """相似圖轉換紀錄的建立時間（ISO 格式字串）。"""

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