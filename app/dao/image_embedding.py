import json

import pymysql

from entity.image_embedding import ImageEmbedding as ImageEmbeddingEntity
from util.mariadb import mariadb_connection


class ImageEmbedding:
    """image_embedding 表的 DAO / Repository"""

    @staticmethod
    def insert(image_embedding: ImageEmbeddingEntity) -> ImageEmbeddingEntity:
        """新增記錄並回傳完整 Entity (包含 DB 產生的 id, created_at 等)"""
        with mariadb_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:

                if image_embedding.vector_512 is not None:
                    # 將 list[float] 序列化為 JSON array 字串（例如 "[0.1, 0.2, ...]"），
                    # 供下方 SQL 中的 VEC_FromText() 解析並轉換為 MariaDB VECTOR(512) 型別
                    vector_json = json.dumps(image_embedding.vector_512)
                else:
                    # 向量為 None 時，保留 None 讓 VEC_FromText(NULL) 寫入 NULL，
                    # 避免呼叫 json.dumps(None) 產生字面上的 "null" 字串造成型別誤解
                    vector_json = None

                cursor.execute(
                    """
                    INSERT INTO image_embedding (
                        image_id,
                        model_name,
                        vector_512
                    )
                    VALUES (
                        %s, %s, VEC_FromText(%s)
                    )
                    RETURNING
                        id, image_id, model_name,
                        VEC_ToText(vector_512) AS vector_512,
                        created_at, updated_at
                    """,
                    (
                        image_embedding.image_id,
                        image_embedding.model_name,
                        vector_json,
                    ),
                )
                row = cursor.fetchone()
                conn.commit()

                if row is None:
                    raise RuntimeError("INSERT ... RETURNING 未回傳任何資料，請檢查資料庫連線或語法")

                if row["vector_512"] and isinstance(row["vector_512"], str):
                    row["vector_512"] = json.loads(row["vector_512"])

                return ImageEmbeddingEntity(**row)


    @staticmethod
    def search_similar_images_embedding(image_embedding_entity: ImageEmbeddingEntity) -> list[ImageEmbeddingEntity]:
        """使用 MariaDB Vector Search 取得最相似的 Top-K 圖片（排除自己）。"""

        vector_json = json.dumps(image_embedding_entity.vector_512)

        sql = """
            SELECT
                ie.image_id,
                ie.model_name,
                VEC_DISTANCE_COSINE(
                    ie.vector_512,
                    VEC_FromText(%s)
                ) AS distance
            FROM image_embedding ie
            WHERE ie.model_name = %s
              AND ie.image_id != %s
            ORDER BY distance ASC
            LIMIT %s
        """

        with mariadb_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:

                cursor.execute(
                    sql,
                    (
                        vector_json,
                        image_embedding_entity.model_name,
                        image_embedding_entity.image_id,
                        10,
                    ),
                )

                rows = cursor.fetchall()

                return [
                    ImageEmbeddingEntity(**row)
                    for row in rows
                ]