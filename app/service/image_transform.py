import time
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


    def generate(self, init_image_path: Path, style_ref_image: Path) -> Image.Image:

        transform_image_path = self._model.generate(init_image_path, style_ref_image)

        return transform_image_path


    @staticmethod
    def process_image_transform(req: TransformRequest) -> TransformResult:
        """生成風格轉換圖並存檔。"""
        # cost flag
        transform_start = time.perf_counter()

        # get model
        t_model = TransformModelFactory.get_model(req.transform_model)
        svct = ImageTransform(model=t_model)

        # 開始生成圖片
        transform_image = svct.generate(req.req_image , Path(req.style_ref_image))

        # 下載圖片
        transform_result = ImageProcessor.save_image(SaveImageRequest(
            req_image=transform_image,
            category=req.category,
            file_name=req.file_name,
            sub_dir=None,
            convert_jpg=True
        ))

        transform_cost = round(time.perf_counter() - transform_start, 3)
        logger.debug(f"style_ref_image: {req.style_ref_image}, transform_path: {transform_result.path}, transform_md5: {transform_result.md5}")

        return TransformResult(
            transform_path=transform_result.path,
            transform_md5=transform_result.md5,
            transform_cost=transform_cost,
        )