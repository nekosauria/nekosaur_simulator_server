import json

from entity.image import Image
from util.mariadb import get_mariadb_connection


def insert(image: Image) -> int:
    """新增一筆 image 紀錄，回傳新產生的 id

    注意：md5_hash 在新表結構中有 UNIQUE 唯一性約束，
    若寫入重複的 md5_hash 會引發 IntegrityError 異常。
    """
    conn = get_mariadb_connection()
    try:
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

    finally:
        conn.close()  # 歸還連線給連線池，不是真的關閉