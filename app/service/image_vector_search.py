import time

from dto.image_vector_search import VectorSearchRequest, VectorSearchResult
from util.common import common

logger = common.logger


class ImageVectorSearch:

    @staticmethod
    def process_similarity_search(req: VectorSearchRequest) -> VectorSearchResult:
        """向量相似圖搜尋。目前先回傳原圖路徑做為 placeholder，之後接 MariaDB vector search。"""
        start = time.perf_counter()

        # TODO: 接上 MariaDB VECTOR INDEX 相似度查詢
        similar_path = req.ora_path

        cost_time = round(time.perf_counter() - start, 3)
        logger.debug(f"similar_path: {similar_path}, cost_time: {cost_time}")

        return VectorSearchResult(similar_path=similar_path, vector_search_cost=cost_time)