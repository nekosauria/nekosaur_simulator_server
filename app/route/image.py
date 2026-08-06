import json
import time
from pathlib import Path

import PIL.Image

from aop.lock import sqlite_table_lock
from flask import Blueprint, request, jsonify

from dto.image_detection import DetectionRequest
from dto.image_processor import SaveImageRequest
from dto.image_transform import TransformRequest
from dto.image_upload_response import ImageUploadResponse
from dto.image_vector_search import VectorSearchRequest
from dto.lock_config import LockConfig
from entity.image import Image
from entity.sys_state import SysState as SysStateEntity
from service.image_processor import ImageProcessor
from service.image_vector_search import ImageVectorSearch
from service.sys_state import SysState as SysStateService

from util.image import validate_image, collect_image_paths
from const.image_const import ImageConst
from service.image_detection import ImageDetection
from service.image_transform import ImageTransform
from service.image_metadata import ImageMetadata
from util.common import common


config = common.config
logger = common.logger

image_bp = Blueprint("image", __name__)

lock_config = LockConfig(
    lock_class=ImageConst.IMAGE_PROCESS,
    ttl_seconds=int(config.get('lock', 'ttl_seconds')),
    retry_interval=float(config.get('lock', 'retry_interval')),
    timeout=int(config.get('lock', 'timeout')),
    max_concurrent=int(config.get('lock', 'max_concurrent')),
)


@image_bp.route(config.get("api","nekosaur_server_count_prefix"), methods=['GET'])
def get_count():
    # === 取得 api 使用次數 (sqlite) ===
    image_process_count = SysStateService.get_image_process_count(SysStateEntity(lock_class=ImageConst.IMAGE_PROCESS))


    # === 取得參考風格圖 ===
    style_ref_image_paths = Path(config.get('image', "style_ref_image_paths"))
    style_ref_path = collect_image_paths(style_ref_image_paths)


    # === return data ===
    response_data = {
        "image_process_count": image_process_count,
        "style_ref_image_paths": style_ref_path
    }

    # pretty print data
    logger.debug("=== [/count Response Data] ===")
    logger.debug(json.dumps(response_data, indent=2, ensure_ascii=False))

    return jsonify(response_data), 200


@image_bp.route(config.get("api","nekosaur_server_upload_prefix"), methods=['POST'])
@sqlite_table_lock(lock_config)
def upload_image():
    # === 格式校驗 & 取參數 ===
    # api cost flag
    api_start = time.perf_counter()

    # 格式校驗
    ora_file, error, status = validate_image(request.files)
    if error:
        return jsonify({"success": False, "error": error}), status

    # 前端取得參數
    ora_image = PIL.Image.open(ora_file)
    detect_model = request.form.get("detect_model", ImageConst.MODEL_YOLO)
    transform_model = request.form.get("transform_model", ImageConst.MODEL_STABLE_DIFFUSION)
    style_ref_image = request.form.get("style_ref_image", config.get('image', "default_style_ref_img"))
    logger.debug(f"detect_model: {detect_model}, transform_model: {transform_model}")

    # 其他參數
    web_base_url = config.get('server', 'web_base_url')
    web_dns_url = config.get("server", "web_dns_url")
    upload_prefix = config.get("api", "nekosaur_server_upload_prefix")

    try:
        # ===  database 重複驗證 ===
        if False:
            # === 若資料庫已有該圖案 md5, 取已經生成 ora & detect image 節省時間 ===

            image_id = 0
            ora_res = None
            ...


        else:
            # === 原始圖片處理 ===
            # 儲存原圖
            ora_res = ImageProcessor.save_image(SaveImageRequest(
                req_image=ora_image,
                category="user_upload_ora_path",
                file_name=ora_file.filename,
                sub_dir=None,
                convert_jpg=False
            ))
            logger.debug(f"ora_path: {ora_res.path}, ora_md5: {ora_res.md5}")
            # reset image index
            ora_image.seek(0)

            # save image metadata
            image_entity = Image(
                md5_hash=ora_res.md5,
                origin_path=ora_res.path,
                image_source=f'{web_dns_url}{upload_prefix}',
            )
            image_id = ImageMetadata.save_image_metadata(image_entity)


            # === 偵測圖片處理 ===
            # 偵測 && 下載
            detect_res = ImageDetection.process_image_detection(
                DetectionRequest(
                    req_image=ora_image,
                    category="user_upload_detect_path",
                    file_name=ora_file.filename,
                    detect_model=detect_model,
                )
            )

            # save image_detection metadata



        # === vector search ===
        vector_res = ImageVectorSearch.process_similarity_search(
            VectorSearchRequest(
                image_id=0,
                ora_path=ora_res.path
            )
        )



        # === ora 風格轉換 ===
        # 風格轉換 & 下載圖
        ora_transform_res = ImageTransform.process_image_transform(
            TransformRequest(
                req_image=ora_image,
                category="user_upload_transform_path",
                file_name=ora_file.filename,
                transform_model=transform_model,
                style_ref_image=style_ref_image
            )
        )

        # 寫 image_embedding metadata



        # === vector search 風格轉換 ===
        # 風格轉換 & 下載圖

        # 寫 image_embedding metadata


    except ValueError as ve:
        logger.error(f"ValueError: {ve}", exc_info=True)
        return jsonify({"error": str(ve)}), 400

    except Exception as e:
        logger.error(f"Exception: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


    # === 組裝 response ===
    response = ImageUploadResponse(
        success=True,
        detector_image=f"{web_base_url}/{detect_res.detect_path.as_posix()}",
        predict_list=detect_res.predict_list,
        tag_results=detect_res.tag_results,
        detector_image_cost=detect_res.detect_cost,
        similar_image=f"{web_base_url}/{vector_res.similar_path.as_posix()}",
        similar_image_cost=vector_res.vector_search_cost,
        origin_image_transform=f"{web_base_url}/{ora_transform_res.transform_path.as_posix()}",
        origin_image_transform_cost=ora_transform_res.transform_cost,
        similar_image_transform=f"{web_base_url}/{ora_transform_res.transform_path.as_posix()}",
        similar_image_transform_cost=ora_transform_res.transform_cost,
        image_process_count=SysStateService.get_image_process_count(SysStateEntity(lock_class=ImageConst.IMAGE_PROCESS)),
        api_cost=round(time.perf_counter() - api_start, 3),
    )

    logger.debug("=== [/upload Response Data] ===")
    logger.debug(json.dumps(response.to_dict(), indent=2, ensure_ascii=False))

    return jsonify(response.to_dict()), 200


