import random
from pathlib import Path
from PIL import Image

from dto.image_transform import TransformRequest, TransformResult
from model.factory.transform_model_factory import TransformModelFactory
from model.interface.base_transform_model import BaseTransformModel
from util.common import common

from entity.image_transform import ImageTransform as ImageTransformEntity
from dao.image_transform import ImageTransform as ImageTransformDao

logger = common.logger


class ImageTransformModel:

    def __init__(self, model: BaseTransformModel):
        self._model = model


    def start_generate(self, req_image: Image.Image, style_ref_image: Image.Image) -> Image.Image:

        transform_image_path = self._model.generate(req_image, style_ref_image)

        return transform_image_path


class ImageTransform:

    @staticmethod
    def process_image_transform(req: TransformRequest) -> TransformResult:
        """生成風格轉換圖並存檔。"""
        # get model
        t_model = TransformModelFactory.get_model(req.transform_model)
        svct = ImageTransformModel(model=t_model)

        # 確保進模型推論的圖片是 3 channel RGB
        req_image = req.req_image.convert("RGB")
        style_ref_image = Image.open(Path(req.style_ref_path)).convert("RGB")

        # 開始生成圖片
        transform_image = svct.start_generate(req_image , style_ref_image )

        return TransformResult(
            transform_image=transform_image
        )


    @staticmethod
    def save_image_transformation_metadata(image_transform_entity: ImageTransformEntity) -> ImageTransformEntity :
        image_transform_entity = ImageTransformDao.insert(image_transform_entity)

        return image_transform_entity


    @staticmethod
    def get_image_transform_metadata_by_image_id(
            image_id: int,
            transform_model: str,
            style_ref_path: str,
    ) -> ImageTransformEntity | None:

        entity_list = ImageTransformDao.get_image_transforms_list_by_image_id(
            image_id, transform_model, style_ref_path
        )

        if not entity_list:
            return None

        selected = random.choice(entity_list)

        logger.debug(
            "image_transform candidates: %s",
            [
                {
                    "id": item.id,
                    "transform_path": item.transform_path,
                }
                for item in entity_list
            ],
        )

        logger.debug(
            "selected image_transform: id=%s, transform_path=%s",
            selected.id,
            selected.transform_path,
        )

        return selected