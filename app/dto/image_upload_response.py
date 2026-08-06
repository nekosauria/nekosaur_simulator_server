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

    # 偵測結果
    detector_image: str
    """
    偵測結果圖（含 draw box 標註）的對外可存取網址，供前端直接顯示。
    """

    tag_results: dict
    """
    各標籤的信心分數彙總，例如 {"cat": 0.9213}，供前端快速顯示辨識結果。
    """

    predict_list: dict
    """
    完整的模型預測結果列表，包含各標籤對應的信心分數細節。
    """

    detector_image_cost: float
    """
    偵測步驟（含模型推論與存檔）耗費的時間，單位為秒。
    """

    # 相似圖搜尋結果
    similar_image: str
    """
    向量搜尋比對出的最相似圖片對外可存取網址。
    """

    similar_image_cost: float
    """
    向量相似圖搜尋耗費的時間，單位為秒。
    """

    # 風格轉換結果
    origin_image_transform: str
    """
    原圖經風格轉換後的結果圖對外可存取網址。
    """

    origin_image_transform_cost: float
    """
    原圖風格轉換耗費的時間，單位為秒。
    """

    similar_image_transform: str
    """
    相似圖經風格轉換後的結果圖對外可存取網址。
    """

    similar_image_transform_cost: float
    """
    相似圖風格轉換耗費的時間，單位為秒。
    """

    # meta
    image_process_count: int
    """
    目前累計的圖片處理次數，取自 sys_state 表統計，供前端顯示使用量。
    """

    api_cost: float
    """
    本次 /upload 請求從接收到回傳的總耗費時間，單位為秒。
    """

    def to_dict(self) -> dict:
        """將 response 物件序列化為 dict，供 Flask jsonify() 使用。"""
        return {
            "success": self.success,
            "detector_image": self.detector_image,
            "predict_list": self.predict_list,
            "tag_results": self.tag_results,
            "detector_image_cost": self.detector_image_cost,
            "similar_image": self.similar_image,
            "similar_image_cost": self.similar_image_cost,
            "origin_image_transform": self.origin_image_transform,
            "origin_image_transform_cost": self.origin_image_transform_cost,
            "similar_image_transform": self.similar_image_transform,
            "similar_image_transform_cost": self.similar_image_transform_cost,
            "image_process_count": self.image_process_count,
            "api_cost": self.api_cost,
        }