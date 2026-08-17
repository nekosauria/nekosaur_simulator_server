import random
from pathlib import Path
from PIL import Image

from dto.image_processor import SaveImageRequest
from dto.image_transform import TransformRequest, TransformResult
from model.factory.transform_model_factory import TransformModelFactory
from model.interface.base_transform_model import BaseTransformModel
from util.common import common

from service.image_processor import ImageProcessor as ImageProcessorService

from entity.image_transform import ImageTransform as ImageTransformEntity
from dao.image_transform import ImageTransform as ImageTransformDao
from util.image import check_file_exists

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
            is_use: bool,
    ) -> ImageTransformEntity | None:

        entity_list = ImageTransformDao.get_image_transforms_list_by_image_id(
            image_id, transform_model, style_ref_path, is_use
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


    @staticmethod
    def get_or_generate_transform(
            image_entity,
            req_image,
            transform_model: str,
            style_ref_path: str,
            save_category: str,
            is_use: bool,
            is_preprocessed: bool,
    ) -> ImageTransformEntity:
        """
        檢查是否已有可用（is_use=False）的 transform 快取，有則直接回傳，
        沒有則產生一筆新的（推論 → 存檔 → 寫 DB）。

        :param save_category: 存檔分類，決定實體檔案存到哪個 category 目錄
                               （例如 "user_upload_transform_path"、"thecatapi_transform_path"）
        :param is_use: 新產生的這筆紀錄是否標記為「已使用」
                       （使用者當下觸發、立即消費 = True；背景預先產出的快取 = False）
        :param is_preprocessed: 新產生的這筆紀錄是否為「預處理/前端用此值判斷是否為 cache」產生
                                （背景批次任務產出 = True；即時回應使用者請求產出 = False）
        """
        # === 檢查是否已有可用（未使用）的 transform 快取 ===
        existing_transform_entity = ImageTransform.get_image_transform_metadata_by_image_id(
            image_id=image_entity.id,
            transform_model=transform_model,
            style_ref_path=style_ref_path,
            is_use=False,
        )

        # 有快取，檢查實體檔案是否存在
        if existing_transform_entity is not None:
            if check_file_exists(str(existing_transform_entity.transform_path)):
                return existing_transform_entity

            logger.error(
                f"Transform metadata exists (ID: {existing_transform_entity.id}), "
                f"but physical file is missing at: {existing_transform_entity.transform_path}. Regenerating..."
            )

        # === 沒有快取，執行風格轉換模型推論 ===
        transform_res = ImageTransform.process_image_transform(
            TransformRequest(
                req_image=req_image,
                transform_model=transform_model,
                style_ref_path=style_ref_path,
            )
        )

        # === 將轉換後的圖片存檔（依 save_category 決定存放目錄）===
        transform_result = ImageProcessorService.save_image(SaveImageRequest(
            req_image=transform_res.transform_image,
            category=save_category,
            file_name=image_entity.file_name,
            sub_dir=transform_model,
            convert_jpg=True,
        ))

        # === 寫入 image_transform metadata，回傳新建立的 entity ===
        return ImageTransform.save_image_transformation_metadata(
            ImageTransformEntity(
                image_id=image_entity.id,
                md5_hash=transform_result.md5,
                transform_path=transform_result.path,
                transform_model=transform_model,
                style_ref_path=style_ref_path,
                is_use=is_use,
                is_preprocessed=is_preprocessed,
            )
        )