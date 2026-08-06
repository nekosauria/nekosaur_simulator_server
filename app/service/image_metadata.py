from entity.image import Image

from dao.image import insert


class ImageMetadata:
    """
    統一管理圖片落地儲存的路徑慣例與 md5 計算。
    """

    @staticmethod
    def save_image_metadata(image: Image) -> int:
        # add database metadata
        image_id = insert(image)

        return image_id
