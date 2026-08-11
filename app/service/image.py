from entity.image import Image as ImageEntity

from dao.image import Image as ImageDao

class Image:
    """
    統一管理圖片落地儲存的路徑慣例與 md5 計算。
    """

    @staticmethod
    def save_image_metadata(image_entity: ImageEntity) -> ImageEntity:
        # add database metadata
        image_entity = ImageDao.insert(image_entity)

        return image_entity


    @staticmethod
    def get_by_id(image_id: int) -> ImageEntity:
        image_entity = ImageDao.get_by_id(image_id)

        if image_entity is None:
            raise ValueError(
                f"找不到 image_id={image_id} 的圖片"
            )

        return image_entity