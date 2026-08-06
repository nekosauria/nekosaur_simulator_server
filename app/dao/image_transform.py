from entity.image_transform import ImageTransform as ImageTransformEntity
from util.mariadb import mariadb_connection


class ImageTransform:
    """image_transform 表的 DAO / Repository"""
    @staticmethod
    def insert(image_transform: ImageTransformEntity) -> int:
        with mariadb_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO image_transform (
                        image_id,
                        md5_hash,
                        transform_path,
                        transform_model
                    )
                    VALUES (
                        %s, %s, %s, %s
                    )
                    """,
                    (
                        image_transform.image_id,
                        image_transform.md5_hash,
                        str(image_transform.transform_path),
                        image_transform.transform_model,
                    ),
                )
                conn.commit()
                return cursor.lastrowid