from dto.image_embedding import EmbeddingRequest
from util.common import common

logger = common.logger


class ImageEmbedding:


    @staticmethod
    def process_similarity_search(req: EmbeddingRequest) -> None:
        """向量相似圖搜尋。目前先回傳原圖路徑做為 placeholder，之後接 MariaDB vector search。"""

        # TODO: 接上 MariaDB VECTOR INDEX 相似度查詢

        return None