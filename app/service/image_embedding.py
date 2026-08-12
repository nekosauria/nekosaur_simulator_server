import random

import numpy as np

from dto.image_embedding import EmbeddingRequest, EmbeddingResult
from model.interface.base_embedding_model import BaseEmbeddingModel
from util.common import common

import PIL.Image

from model.factory.embedding_model_factory import EmbeddingModelFactory

from entity.image_embedding import ImageEmbedding as ImageEmbeddingEntity
from dao.image_embedding import ImageEmbedding as ImageEmbeddingDao


config = common.config
logger = common.logger

class ImageEmbeddingModel:

    def __init__(self, model: BaseEmbeddingModel):
        self._model = model

    def start_encode_image(self,req_image: PIL.Image.Image) -> np.ndarray:

        image_embedding_vector = self._model.encode_image(req_image)

        return image_embedding_vector


class ImageEmbedding:
    @staticmethod
    def process_image_embedding(req: EmbeddingRequest) -> EmbeddingResult:
        """向量相似圖搜尋。目前先回傳原圖路徑做為 placeholder，之後接 MariaDB vector search。"""
        # 取參數
        req_image = req.req_image
        embedding_model = req.embedding_model

        # 取得模型
        e_model = EmbeddingModelFactory.get_model(embedding_model)
        svce = ImageEmbeddingModel(model=e_model)

        # 取得模型向量
        image_embedding_vector = svce.start_encode_image(req_image)

        # 取得 image Vector
        return EmbeddingResult(
            image_embedding_vector=image_embedding_vector.tolist(),  # np.ndarray -> list[float]
        )

    @staticmethod
    def get_image_embedding_metadata_by_image_id(image_id: int, embedding_model: str) -> ImageEmbeddingEntity:
        image_embedding_entity = ImageEmbeddingDao.get_image_embedding_by_image_id(image_id, embedding_model)

        return image_embedding_entity

    @staticmethod
    def save_image_embedding_metadata(image_embedding_entity: ImageEmbeddingEntity) -> ImageEmbeddingEntity :
        image_embedding_entity =ImageEmbeddingDao.insert(image_embedding_entity)

        return image_embedding_entity

    @staticmethod
    def search_similar_images_embedding(image_embedding_entity: ImageEmbeddingEntity) -> ImageEmbeddingEntity:
        # 查詢最相似的前10名
        image_embedding_entity_list = (
            ImageEmbeddingDao.search_similar_images_embedding(
                image_embedding_entity
            )
        )

        if not image_embedding_entity_list:
            logger.debug(
                "no similar image found for image_id=%s, model_name=%s",
                image_embedding_entity.image_id,
                image_embedding_entity.model_name,
            )
            return ImageEmbeddingEntity(
                id=None,
                image_id=None,
                model_name=None,
                vector_512=None,
                distance=None,
                created_at=None,
                updated_at=None,
            )

        # 隨機挑選一筆達成隨機性
        selected_image_embedding = random.choice(image_embedding_entity_list)

        logger.debug(
            "similar image candidates: %s",
            [
                {
                    "image_id": item.image_id,
                    "distance": item.distance,
                }
                for item in image_embedding_entity_list
            ],
        )

        logger.debug(
            "selected similar image: image_id=%s, distance=%s",
            selected_image_embedding.image_id,
            selected_image_embedding.distance,
        )

        return selected_image_embedding