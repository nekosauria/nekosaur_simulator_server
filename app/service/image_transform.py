from pathlib import Path
from PIL import Image

from dto.image_processor import SaveImageRequest
from dto.image_transform import TransformRequest, TransformResult
from model.factory.transform_model_factory import TransformModelFactory
from model.interface.base_transform_model import BaseTransformModel
from service.image_processor import ImageProcessor
from util.common import common

logger = common.logger


class ImageTransform:

    def __init__(self, model: BaseTransformModel):
        self._model = model


    def generate(self, req_image: Image.Image, style_ref_image: Image.Image) -> Image.Image:

        transform_image_path = self._model.generate(req_image, style_ref_image)

        return transform_image_path


    @staticmethod
    def process_image_transform(req: TransformRequest) -> TransformResult:
        """生成風格轉換圖並存檔。"""
        # get model
        t_model = TransformModelFactory.get_model(req.transform_model)
        svct = ImageTransform(model=t_model)

        # 確保進模型推論的圖片是 3 channel RGB
        req_image = req.req_image.convert("RGB")
        style_ref_image = Image.open(Path(req.style_ref_image)).convert("RGB")

        # 開始生成圖片
        transform_image = svct.generate(req_image , style_ref_image )

        return TransformResult(
            transform_image=transform_image
        )