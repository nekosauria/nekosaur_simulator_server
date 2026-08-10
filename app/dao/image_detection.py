import json

import pymysql

from entity.image_detection import ImageDetection as ImageDetectionEntity
from util.mariadb import mariadb_connection


class ImageDetection:
    """image_detection 表的 DAO / Repository"""

    @staticmethod
    def insert(image_detection: ImageDetectionEntity) -> ImageDetectionEntity:
        """新增記錄並回傳完整 Entity (包含 DB 產生的 id, created_at 等)"""
        with mariadb_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:

                predict_list_json = (
                    json.dumps(image_detection.predict_list, ensure_ascii=False)
                    if image_detection.predict_list is not None
                    else None
                )
                tag_results_json = (
                    json.dumps(image_detection.tag_results, ensure_ascii=False)
                    if image_detection.tag_results is not None
                    else None
                )

                cursor.execute(
                    """
                    INSERT INTO image_detection (
                        image_id,
                        md5_hash,
                        detect_path,
                        detect_model,
                        has_cat,
                        is_preprocessed,
                        predict_list,
                        tag_results
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING
                        id, image_id, md5_hash, detect_path, detect_model,
                        has_cat, is_preprocessed, predict_list, tag_results,
                        created_at, updated_at
                    """,
                    (
                        image_detection.image_id,
                        image_detection.md5_hash,
                        str(image_detection.detect_path) if image_detection.detect_path is not None else None,
                        image_detection.detect_model,
                        image_detection.has_cat,
                        image_detection.is_preprocessed,
                        predict_list_json,
                        tag_results_json,
                    ),
                )
                row = cursor.fetchone()
                conn.commit()

                if row["predict_list"] and isinstance(row["predict_list"], str):
                    row["predict_list"] = json.loads(row["predict_list"])
                if row["tag_results"] and isinstance(row["tag_results"], str):
                    row["tag_results"] = json.loads(row["tag_results"])

                return ImageDetectionEntity(**row)