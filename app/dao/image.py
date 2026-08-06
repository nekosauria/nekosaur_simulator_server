import json

from entity.image import Image as ImageEntity
from util.mariadb import mariadb_connection


class Image:
    """image 表的 DAO / Repository"""
    @staticmethod
    def insert(image: ImageEntity) -> int:
        with mariadb_connection() as conn:
            with conn.cursor() as cursor:

                raw_source_json = (
                    json.dumps(image.raw_source, ensure_ascii=False)
                    if image.raw_source is not None
                    else None
                )

                cursor.execute(
                    """
                    INSERT INTO image (
                        image_source,
                        raw_source,
                        md5_hash,
                        origin_path
                    )
                    VALUES (
                        %s, %s, %s, %s
                    )
                    """,
                    (
                        image.image_source,
                        raw_source_json,
                        image.md5_hash,
                        str(image.origin_path),
                    ),
                )
                conn.commit()
                return cursor.lastrowid