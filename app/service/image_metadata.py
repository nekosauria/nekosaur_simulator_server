from entity.image import Image as ImageEntity
from entity.image_detection import ImageDetection as ImageDetectionEntity
from entity.image_transform import ImageTransform as ImageTransformEntity
from entity.image_embedding import ImageEmbedding as ImageEmbeddingEntity

from dao.image import Image as ImageDao
from dao.image_detection import ImageDetection as ImageDetectionDao
from dao.image_transform import ImageTransform as ImageTransformDao
from dao.image_embedding import ImageEmbedding as ImageEmbeddingDao

class ImageMetadata:
    """
    統一管理圖片落地儲存的路徑慣例與 md5 計算。
    """

    @staticmethod
    def save_image_metadata(image_entity: ImageEntity) -> ImageEntity:
        # add database metadata
        image_entity = ImageDao.insert(image_entity)

        return image_entity


    @staticmethod
    def save_image_detection_metadata(image_detection_entity: ImageDetectionEntity) -> ImageDetectionEntity :
        image_detection_entity = ImageDetectionDao.insert(image_detection_entity)

        return image_detection_entity


    @staticmethod
    def save_image_transformation_metadata(image_transform_entity: ImageTransformEntity) -> ImageTransformEntity :
        image_transform_entity = ImageTransformDao.insert(image_transform_entity)

        return image_transform_entity


    @staticmethod
    def save_image_embedding_metadata(image_embedding_entity: ImageEmbeddingEntity) -> ImageEmbeddingEntity :
        image_embedding_entity =ImageEmbeddingDao.insert(image_embedding_entity)

        return image_embedding_entity

