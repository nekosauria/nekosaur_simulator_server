from entity.image import Image as ImageEntity
from entity.image_detection import ImageDetection as ImageDetectionEntity
from entity.image_transform import ImageTransform as ImageTransformEntity

from dao.image import Image as ImageDao
from dao.image_detection import ImageDetection as ImageDetectionDao
from dao.image_transform import ImageTransform as ImageTransformDao

class ImageMetadata:
    """
    統一管理圖片落地儲存的路徑慣例與 md5 計算。
    """

    @staticmethod
    def save_image_metadata(image_entity: ImageEntity) -> int:
        # add database metadata
        image_id = ImageDao.insert(image_entity)

        return image_id


    @staticmethod
    def save_image_detection_metadata(image_detection_entity: ImageDetectionEntity) -> int :
        image_detection_id = ImageDetectionDao.insert(image_detection_entity)

        return image_detection_id


    @staticmethod
    def save_image_transformation_metadata(image_transform_entity: ImageTransformEntity) -> int :
        image_transform_id = ImageTransformDao.insert(image_transform_entity)

        return image_transform_id
