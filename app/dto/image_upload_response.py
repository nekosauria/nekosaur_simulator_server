# dto/image_upload_response.py
from dataclasses import dataclass


@dataclass
class ImageUploadResponse:
    """
    /upload 端點對外回傳的 response schema。
    集中管理 API 回傳格式，避免 controller 內直接組 dict 導致欄位名稱漂移不受型別檢查保護。
    """

    success: bool

    # 偵測結果
    detector_image: str
    predict_list: dict
    tag_results: dict
    detector_image_cost: float

    # 相似圖搜尋結果
    similar_image: str
    similar_image_cost: float

    # 風格轉換結果
    origin_image_transform: str
    origin_image_transform_cost: float
    similar_image_transform: str
    similar_image_transform_cost: float

    # meta
    image_process_count: int
    api_cost: float

    def to_dict(self) -> dict:
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