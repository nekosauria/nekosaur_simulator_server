import json

import pymysql

from entity.image import Image as ImageEntity
from util.mariadb import mariadb_connection


class Image:
    """image 表的 DAO / Repository"""

    @staticmethod
    def insert(image: ImageEntity) -> ImageEntity:
        """新增記錄並回傳完整 Entity (包含 DB 產生的 id, created_at 等)"""
        with mariadb_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                raw_source_json = (
                    json.dumps(image.raw_source, ensure_ascii=False)
                    if image.raw_source is not None
                    else None
                )

                cursor.execute(
                    """
                    INSERT INTO image (
                        md5_hash, origin_path, image_source, raw_source,
                        is_deleted, deleted_at, last_checked_at
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING 
                        id, md5_hash, origin_path, image_source, raw_source,
                        is_deleted, deleted_at, last_checked_at, created_at, updated_at
                    """,
                    (
                        image.md5_hash,
                        str(image.origin_path),
                        image.image_source,
                        raw_source_json,
                        image.is_deleted,
                        image.deleted_at,
                        image.last_checked_at,
                    ),
                )
                row = cursor.fetchone()
                conn.commit()

                if row["raw_source"] and isinstance(row["raw_source"], str):
                    row["raw_source"] = json.loads(row["raw_source"])

                return ImageEntity(**row)

    @staticmethod
    def get_by_id(image_id: int) -> ImageEntity | None:
        """依 image.id 取得圖片 Entity；不存在時回傳 None。"""
        with mariadb_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        md5_hash,
                        origin_path,
                        image_source,
                        raw_source,
                        is_deleted,
                        deleted_at,
                        last_checked_at,
                        created_at,
                        updated_at
                    FROM image
                    WHERE id = %s
                    """,
                    (image_id,),
                )

                row = cursor.fetchone()

                if row is None:
                    return None

                if row["raw_source"] and isinstance(row["raw_source"], str):
                    row["raw_source"] = json.loads(row["raw_source"])

                return ImageEntity(**row)