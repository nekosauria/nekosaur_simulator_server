import pymysql

from entity.image import Image as ImageEntity
from dao.image import Image as ImageDao


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