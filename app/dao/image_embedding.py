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
                vector_json = (
                    json.dumps(image_embedding.vector_512)
                    if image_embedding.vector_512 is not None
                    else None
                )

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