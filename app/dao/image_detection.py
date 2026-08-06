import json

from entity.image_detection import ImageDetection as ImageDetectionEntity
from util.mariadb import mariadb_connection


class ImageDetection:
    """image_detection 表的 DAO / Repository"""
    @staticmethod
    def insert(image_detection: ImageDetectionEntity) -> int:
        with mariadb_connection() as conn:
            with conn.cursor() as cursor:

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
                        predict_list,
                        tag_results
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s
                    )
                    """,
                    (
                        image_detection.image_id,
                        image_detection.md5_hash,
                        str(image_detection.detect_path) if image_detection.detect_path is not None else None,
                        image_detection.detect_model,
                        predict_list_json,
                        tag_results_json,
                    ),
                )
                conn.commit()
                return cursor.lastrowid