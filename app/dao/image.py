import json
from datetime import datetime

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
                        md5_hash, file_name, origin_path, image_source, raw_source,
                        is_deleted, deleted_at, last_checked_at
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING 
                        id, md5_hash, file_name, origin_path, image_source, raw_source,
                        is_deleted, deleted_at, last_checked_at, created_at, updated_at
                    """,
                    (
                        image.md5_hash,
                        image.file_name,
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
    def get_image_by_id(image_id: int) -> ImageEntity | None:
        """依 image.id 取得圖片 Entity；不存在時回傳 None。"""
        with mariadb_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        md5_hash,
                        file_name,
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

    @staticmethod
    def get_by_md5_hash(md5_hash: str) -> ImageEntity | None:
        """依 md5_hash 取得圖片 Entity；不存在時回傳 None。"""
        with mariadb_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        md5_hash,
                        file_name,
                        origin_path,
                        image_source,
                        raw_source,
                        is_deleted,
                        deleted_at,
                        last_checked_at,
                        created_at,
                        updated_at
                    FROM image
                    WHERE md5_hash = %s
                    """,
                    (md5_hash,),
                )

                row = cursor.fetchone()

                if row is None:
                    return None

                if row["raw_source"] and isinstance(row["raw_source"], str):
                    row["raw_source"] = json.loads(row["raw_source"])

                return ImageEntity(**row)

    @staticmethod
    def soft_delete_image(image_id: int) -> None:
        """將 image 標記為已刪除（is_deleted=TRUE, deleted_at=now()），不刪除實體資料列"""
        with mariadb_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE image
                    SET is_deleted = TRUE,
                        deleted_at = NOW(),
                        last_checked_at = NOW()
                    WHERE id = %s
                    """,
                    (image_id,),
                )
                conn.commit()

    @staticmethod
    def get_images_created_between(
            after: datetime,
            before: datetime,
            limit: int,
    ) -> list[ImageEntity]:
        """查詢 created_at 落在 [after, before) 區間內、尚未軟刪除的圖片，
        依 created_at 由舊到新排序，最多回傳 limit 筆。"""
        with mariadb_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        md5_hash,
                        file_name,
                        origin_path,
                        image_source,
                        raw_source,
                        is_deleted,
                        deleted_at,
                        last_checked_at,
                        created_at,
                        updated_at
                    FROM image
                    WHERE created_at >= %s
                      AND created_at < %s
                      AND is_deleted = FALSE
                    ORDER BY created_at ASC
                    LIMIT %s
                    """,
                    (after, before, limit),
                )

                rows = cursor.fetchall()

                for row in rows:
                    if row["raw_source"] and isinstance(row["raw_source"], str):
                        row["raw_source"] = json.loads(row["raw_source"])

                return [ImageEntity(**row) for row in rows]

    @staticmethod
    def update_last_checked_at(image_id: int) -> None:
        """更新指定圖片的 last_checked_at 時間戳記；若未傳入時間則預設為目前時間 (NOW())"""
        with mariadb_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE image
                    SET last_checked_at = NOW()
                    WHERE id = %s
                    """,
                    (image_id,),
                )

                conn.commit()