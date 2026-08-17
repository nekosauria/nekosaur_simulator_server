from datetime import datetime

import pymysql

from dto.image_processor import SaveImageRequest
from entity.image import Image as ImageEntity
from dao.image import Image as ImageDao
from util.common import common

from service.image_processor import ImageProcessor as ImageProcessorService

# get conf
config = common.config
logger = common.logger


class Image:

    @staticmethod
    def get_image_metadata_by_id(
            image_id: int,
    ) -> ImageEntity | None:
        image_entity = ImageDao.get_image_by_id(image_id)

        if image_entity is None:
            return None

        return image_entity


    @staticmethod
    def get_image_metadata_by_md5_hash(
            md5_hash: str,
    ) -> ImageEntity | None:
        image_entity = ImageDao.get_by_md5_hash(md5_hash)

        if image_entity is None:
            return None

        return image_entity


    @staticmethod
    def insert_image_metadata(
            image_entity: ImageEntity,
    ) -> ImageEntity:

        try:
            return ImageDao.insert(image_entity)

        except pymysql.IntegrityError:
            # if 另一個 request 已經先 INSERT
            existing_image = ImageDao.get_by_md5_hash(
                image_entity.md5_hash
            )

            if existing_image is None:
                raise

            return existing_image


    @staticmethod
    def soft_delete_image(image_id: int) -> None:
        """軟刪除 image（設 is_deleted=True, deleted_at=now()）"""
        ImageDao.soft_delete_image(image_id)
        logger.debug(f"soft_delete_image: image_id={image_id}")


    @staticmethod
    def update_last_checked_at(image_id: int) -> None:
        """更新最後巡檢時間"""
        ImageDao.update_last_checked_at(image_id)
        logger.debug(f"update_last_checked_at: image_id={image_id}")


    @staticmethod
    def get_images_created_between(
            after: datetime,
            before: datetime,
            limit: int,
    ) -> list[ImageEntity]:
        """取得 created_at 落在 [after, before) 區間內、尚未軟刪除的圖片（分批）"""
        image_entities = ImageDao.get_images_created_between(after, before, limit)

        logger.debug(
            f"get_images_created_between: after={after}, before={before}, "
            f"limit={limit}, found={len(image_entities)}"
        )

        return image_entities


    @staticmethod
    def save_and_insert_image(
            req_image,
            file_name: str,
            save_category: str,
            image_source: str,
            raw_source,
    ) -> ImageEntity:
        """
        存檔並寫入 image metadata（原圖處理共用邏輯）。

        :param save_category: 存檔分類，決定實體檔案存到哪個 category 目錄
                               （例如 "thecatapi_origin_path"、"user_upload_origin_path"）
        :param image_source: 圖片來源說明（例如 thecatapi 的 API url，或使用者上傳的 web_dns_url+prefix）
        :param raw_source: 原始來源備查資料（第三方 API 回傳的原始 JSON，或使用者上傳的檔名）
        """
        # === 存檔 ===
        save_result = ImageProcessorService.save_image(SaveImageRequest(
            req_image=req_image,
            category=save_category,
            file_name=file_name,
            sub_dir=None,
            convert_jpg=False,
        ))
        logger.debug(f"save_and_insert_image: path={save_result.path}, md5={save_result.md5}")

        # === 寫入 image metadata ===
        return Image.insert_image_metadata(
            ImageEntity(
                md5_hash=save_result.md5,
                origin_path=save_result.path,
                image_source=image_source,
                file_name=file_name,
                raw_source=raw_source,
                is_deleted=False,
            )
        )