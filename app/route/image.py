import json
from pathlib import Path

from PIL import Image

from aop.lock import sqlite_table_lock
from flask import Blueprint, request, jsonify

from util.image import validate_image, collect_image_paths
from const.image_const import ImageConst
from util.common import common

from dto.image_detection import DetectionRequest
from dto.image_processor import SaveImageRequest
from dto.image_transform import TransformRequest
from dto.image_embedding import EmbeddingRequest
from dto.image_upload import ImageUploadResponse
from dto.lock_config import LockConfig

from service.image_detection import ImageDetection as ImageDetectionService
from service.image_transform import ImageTransform as ImageTransformService
from service.image import Image as ImageService
from service.image_processor import ImageProcessor as ImageProcessorService
from service.image_embedding import ImageEmbedding as ImageEmbeddingService
from service.sys_state import SysState as SysStateService

from entity.image import Image as ImageEntity
from entity.image_detection import ImageDetection as ImageDetectionEntity
from entity.image_transform import ImageTransform as ImageTransformEntity
from entity.image_embedding import ImageEmbedding as ImageEmbeddingEntity

from entity.sys_state import SysState as SysStateEntity
from util.step_timer import StepTimer


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



@image_bp.route(config.get("api", "nekosaur_server_count_prefix"), methods=['GET'])
def get_count():
    timer = StepTimer()

    with timer.track("api_total_cost"):
        # === 取得 api 使用次數 (sqlite) ===
        image_process_count = SysStateService.get_image_process_count(SysStateEntity(lock_class=ImageConst.IMAGE_PROCESS))

        # === 取得參考風格圖 ===
        style_ref_image_path = Path(config.get('image', "style_ref_image_path"))
        style_ref_image_paths = collect_image_paths(style_ref_image_path)


    # === return data ===
    response_data = {
        "image_process_count": image_process_count,
        "style_ref_image_paths": style_ref_image_paths,
        "api_cost": timer.costs["api_total_cost"]
    }

    # pretty print data
    logger.debug("=== [/count Response Data] ===")
    logger.debug(json.dumps(response_data, indent=2, ensure_ascii=False))

    return jsonify(response_data), 200


@image_bp.route(config.get("api","nekosaur_server_upload_prefix"), methods=['POST'])
@sqlite_table_lock(lock_config)
def upload_image():
    timer = StepTimer()

#  === start api ===
# ======================================================================================================================
    # 全域 API 開始計時
    with timer.track("api_total_cost"):

        # === 格式校驗 & 取參數 ===
        with timer.track("image_validate_cost"):
            # 格式校驗
            origin_file, error, status = validate_image(request.files)
            if error:
                return jsonify({"success": False, "error": error}), status

            # 前端取得參數
            origin_image = Image.open(origin_file)
            detect_model = request.form.get("detect_model", ImageConst.MODEL_YOLO)
            transform_model = request.form.get("transform_model", ImageConst.MODEL_STABLE_DIFFUSION)
            style_ref_image = request.form.get("style_ref_image", config.get('image', "default_style_ref_img"))
            logger.debug(f"detect_model: {detect_model}, transform_model: {transform_model}")

            # 其他參數
            web_base_url = config.get('server', 'web_base_url')
            web_dns_url = config.get("server", "web_dns_url")
            upload_prefix = config.get("api", "nekosaur_server_upload_prefix")
            embedding_model = ImageConst.MODEL_CLIP_VIT_B_32


#  === save origin image & get similar info ===
# ======================================================================================================================
        #  === 原圖處理 ===
        with timer.track("image_embedding_cost"):
            # save origin image
            origin_result = ImageProcessorService.save_image(
                SaveImageRequest(
                    req_image=origin_image,
                    category="user_upload_origin_path",
                    file_name=origin_file.filename,
                    sub_dir=None,
                    convert_jpg=False
                )
            )
            logger.debug(f"origin_path: {origin_result.path}, origin_md5: {origin_result.md5}")

            # save origin image metadata
            origin_image_entity = ImageService.save_image_metadata(
                ImageEntity(
                    md5_hash=origin_result.md5,
                    origin_path=origin_result.path,
                    image_source=f'{web_dns_url}{upload_prefix}',
                    raw_source=None,
                    is_deleted=False
                )
            )

            # get origin image_embedding vector
            origin_embedding_res = ImageEmbeddingService.process_image_embedding(
                EmbeddingRequest(
                    req_image=origin_image,
                    embedding_model=embedding_model,
                )
            )

            # save origin image_embedding metadata
            origin_image_embedding_entity = ImageEmbeddingService.save_image_embedding_metadata(
                ImageEmbeddingEntity(
                    image_id=origin_image_entity.id,
                    model_name=embedding_model,
                    vector_512=origin_embedding_res.image_embedding_vector
                )
            )

            #  === 相似圖處理 ===
            # search similar embedding_image entity
            similar_image_embedding_entity = ImageEmbeddingService.search_similar_images_embedding(
                origin_image_embedding_entity
            )

            # similar image entity
            similar_image_entity = ImageService.get_by_id(
                similar_image_embedding_entity.image_id
            )
            similar_image = Image.open(Path(similar_image_entity.origin_path))


# === 寫入 origin detect info ===
# ======================================================================================================================
        # origin image detect
        with timer.track("origin_detector_cost"):
            # draw predict detect image
            origin_detect_res = ImageDetectionService.process_image_detection(
                DetectionRequest(
                    req_image=origin_image,
                    detect_model=detect_model,
                )
            )

            # save origin detect image
            origin_detect_result = ImageProcessorService.save_image(SaveImageRequest(
                req_image=origin_detect_res.detect_image,
                category="user_upload_detect_path",
                file_name=origin_file.filename,
                sub_dir=detect_model,
                convert_jpg=True
            ))

            # save origin image_detection metadata
            origin_image_detection_entity = ImageDetectionService.save_image_detection_metadata(
                ImageDetectionEntity(
                    image_id=origin_image_entity.id,
                    md5_hash=origin_detect_result.md5,
                    detect_path=origin_detect_result.path,
                    detect_model=detect_model,
                    predict_list=origin_detect_res.predict_list,
                    tag_results=origin_detect_res.tag_results,
                )
            )


# === 寫入 similar detect info ===
# ======================================================================================================================
            with timer.track("similar_detect_cost"):
                # draw similar detect image
                similar_detect_res = ImageDetectionService.process_image_detection(
                DetectionRequest(
                    req_image=similar_image,
                    detect_model=detect_model,
                )
            )

                # save similar detect image
                similar_detect_result = ImageProcessorService.save_image(SaveImageRequest(
                    req_image=similar_detect_res.detect_image,
                    category="thecatapi_detect_path",
                    file_name=origin_file.filename,
                    sub_dir=detect_model,
                    convert_jpg=True
                ))

                # save similar image_detection metadata
                similar_image_detection_entity = ImageDetectionService.save_image_detection_metadata(
                    ImageDetectionEntity(
                        image_id=similar_image_entity.id,
                        md5_hash=similar_detect_result.md5,
                        detect_path=similar_detect_result.path,
                        detect_model=detect_model,
                        predict_list=similar_detect_res.predict_list,
                        tag_results=similar_detect_res.tag_results,
                    )
                )



#  === 寫入 origin transform info ===
# ======================================================================================================================
        with timer.track("origin_transform_cost"):
            # 風格轉換圖生成
            origin_transform_res = ImageTransformService.process_image_transform(
                TransformRequest(
                    req_image=origin_image,
                    transform_model=transform_model,
                    style_ref_image=style_ref_image
                )
            )

            # 下載圖片
            origin_transform_result = ImageProcessorService.save_image(SaveImageRequest(
                req_image=origin_transform_res.transform_image,
                category="user_upload_transform_path",
                file_name=origin_file.filename,
                sub_dir=transform_model,
                convert_jpg=True
            ))

            # save image_transform metadata
            origin_transform_entity = ImageTransformService.save_image_transformation_metadata(
                ImageTransformEntity(
                    image_id=origin_image_entity.id,
                    md5_hash=origin_transform_result.md5,
                    transform_path=origin_transform_result.path,
                    transform_model=transform_model,
                )
            )


#  === 寫入 similar transform info ===
# ======================================================================================================================
            with timer.track("similar_transform_cost"):
                # 風格轉換 & 下載圖
                similar_transform_res = ImageTransformService.process_image_transform(
                    TransformRequest(
                        req_image=similar_image,
                        transform_model=transform_model,
                        style_ref_image=style_ref_image
                    )
                )

                # 下載圖片
                similar_transform_result = ImageProcessorService.save_image(SaveImageRequest(
                    req_image=similar_transform_res.transform_image,
                    category="thecatapi_transform_path",
                    file_name=similar_image.filename,
                    sub_dir=transform_model,
                    convert_jpg=True
                ))

                # 寫 image_transform metadata
                similar_transform_entity = ImageTransformService.save_image_transformation_metadata(
                    ImageTransformEntity(
                        image_id=similar_image_entity.id,
                        md5_hash=similar_transform_result.md5,
                        transform_path=similar_transform_result.path,
                        transform_model=transform_model,
                    )
                )



    # === 跳出 api_total_cost 的 with 區塊後，計時器才正式完成並寫入 api_total_cost ===



# === 組裝 response ===
# ======================================================================================================================
    response = ImageUploadResponse(
        # --- Origin Detector ---
        origin_image_path=f"{web_base_url}/{origin_image_entity.origin_path.as_posix()}",
        origin_detect_path=f"{web_base_url}/{origin_image_detection_entity.detect_path.as_posix()}",
        origin_detect_model=detect_model,
        origin_has_cat=origin_image_detection_entity.has_cat,
        origin_detect_is_preprocessed=origin_image_detection_entity.is_preprocessed,
        origin_predict_list=origin_image_detection_entity.predict_list,
        origin_tag_results=origin_image_detection_entity.tag_results,
        origin_detect_created_at=origin_image_detection_entity.created_at,

        # --- Similar Detector ---
        similar_image_path=f"{web_base_url}/{similar_image_entity.origin_path.as_posix()}",
        similar_detect_path=f"{web_base_url}/{similar_image_detection_entity.detect_path.as_posix()}",
        similar_detect_model=detect_model,
        similar_has_cat=similar_image_detection_entity.has_cat,
        similar_is_preprocessed=similar_image_detection_entity.is_preprocessed,
        similar_predict_list=similar_image_detection_entity.predict_list,
        similar_tag_results=similar_image_detection_entity.tag_results,
        similar_similar_created_at=similar_image_detection_entity.created_at,

        # --- Origin Transform ---
        origin_transform_path=f"{web_base_url}/{origin_transform_entity.transform_path.as_posix()}",
        origin_transform_model=transform_model,
        origin_transform_is_preprocessed=origin_transform_entity.is_preprocessed,
        origin_transform_created_at=origin_transform_entity.created_at,

        # --- Similar Transform ---
        similar_transform_path=f"{web_base_url}/{similar_transform_entity.transform_path.as_posix()}",
        similar_transform_model=transform_model,
        similar_transform_is_preprocessed=similar_transform_entity.is_preprocessed,
        similar_transform_created_at=similar_transform_entity.created_at,

        # HTTP stat
        success=True,

        # --- Metrics & System ---
        image_process_count=SysStateService.get_image_process_count(
            SysStateEntity(lock_class=ImageConst.IMAGE_PROCESS),
        ),
        image_validate_cost=timer.costs.get("image_validate_cost"),
        image_embedding_cost=timer.costs.get("image_embedding_cost"),
        origin_detector_cost=timer.costs.get("origin_detector_cost"),
        similar_detector_cost=timer.costs.get("similar_detect_cost"),
        origin_transform_cost=timer.costs.get("origin_transform_cost"),
        similar_transform_cost=timer.costs.get("similar_transform_cost"),
        api_cost=timer.costs.get("api_total_cost"),
    )

    logger.debug("=== [/upload Response Data] ===")
    logger.debug(
        json.dumps(response.to_dict(), indent=2, ensure_ascii=False, default=str)
    )

    return jsonify(response.to_dict()), 200