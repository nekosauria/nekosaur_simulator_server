import pymysql

from entity.image_transform import ImageTransform as ImageTransformEntity
from util.mariadb import mariadb_connection


class ImageTransform:
    """image_transform 表的 DAO / Repository"""

    @staticmethod
    def insert(image_transform: ImageTransformEntity) -> ImageTransformEntity:
        """新增記錄並回傳完整 Entity (包含 DB 產生的 id, created_at 等)"""
        with mariadb_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    """
                    INSERT INTO image_transform (
                        image_id,
                        md5_hash,
                        transform_path,
                        transform_model,
                        style_ref_path,
                        is_use,
                        is_preprocessed
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING
                        id, image_id, md5_hash, transform_path, transform_model,
                        style_ref_path, is_use, is_preprocessed,
                        created_at, updated_at
                    """,
                    (
                        image_transform.image_id,
                        image_transform.md5_hash,
                        str(image_transform.transform_path),
                        image_transform.transform_model,
                        str(image_transform.style_ref_path),
                        image_transform.is_use,
                        image_transform.is_preprocessed,
                    ),
                )
                row = cursor.fetchone()
                conn.commit()

                return ImageTransformEntity(**row)

    @staticmethod
    def get_image_transforms_list_by_image_id(
            image_id: int,
            transform_model: str,
            style_ref_path: str,
            is_use: bool,
    ) -> list[ImageTransformEntity]:
        """依 image_id + transform_model + style_ref_path + is_use 查詢
        image_transform 記錄"""
        with mariadb_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT
                        id, image_id, md5_hash, transform_path, transform_model,
                        style_ref_path, is_use, is_preprocessed,
                        created_at, updated_at
                    FROM image_transform
                    WHERE image_id = %s
                      AND transform_model = %s
                      AND style_ref_path = %s
                      AND is_use = %s
                    """,
                    (image_id, transform_model, style_ref_path, is_use),
                )
                rows = cursor.fetchall()

                return [ImageTransformEntity(**row) for row in rows]