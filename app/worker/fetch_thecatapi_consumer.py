import json
import logging
import time
from pathlib import Path

from PIL import Image

from const.image_const import ImageConst
from util.common import common

from dto.image_detection import DetectionRequest
from dto.image_processor import SaveImageRequest
from dto.image_transform import TransformRequest
from dto.image_embedding import EmbeddingRequest

from service.image import Image as ImageService
from service.image_detection import ImageDetection as ImageDetectionService
from service.image_transform import ImageTransform as ImageTransformService
from service.image_embedding import ImageEmbedding as ImageEmbeddingService
from service.image_processor import ImageProcessor as ImageProcessorService

from entity.image_detection import ImageDetection as ImageDetectionEntity
from entity.image_transform import ImageTransform as ImageTransformEntity
from entity.image_embedding import ImageEmbedding as ImageEmbeddingEntity
from util.device import log_device_memory, clear_device_cache, get_gpu_device
from util.step_timer import StepTimer

from worker.base_consumer import BaseConsumer, PermanentProcessingError

logger = common.logger
config = common.config
gpu_device = get_gpu_device()
embedding_model = ImageConst.MODEL_CLIP_VIT_B_32
style_ref_path = config.get('image', "default_style_ref_path")

# GPU 降溫休息秒數，每處理完一筆訊息後 sleep ，避免連續高負載導致過熱/降頻
gpu_rest_seconds = float(config.get("rabbitmq", "fetch_thecatapi_consumer_rest_time"))


class FetchThecatapiConsumer(BaseConsumer[int]): # int = 這個 consumer 的訊息解析完後長什麼樣子

    @property
    def queue_name(self) -> str:
        return config.get("rabbitmq", "fetch_thecatapi_queue_name")

    @property
    def prefetch_count(self) -> int:
        return 1

    def parse_payload(self, body: bytes) -> int:
        payload = json.loads(body.decode("utf-8"))
        return payload["image_id"]

    def handle_message(self, image_id: int, timer: StepTimer) -> None:
        cost_id_str = f"image_id: {image_id}, fetch_thecatapi_consumer_cost"

        with timer.track(cost_id_str):

# === 取得 image entity（含永久性失敗檢查）===
# ======================================================================================================================
            fetch_image_entity = ImageService.get_image_metadata_by_id(image_id)

            if fetch_image_entity is None:
                # DB 查無此紀錄，重試也不會有結果，屬於永久性失敗，不 requeue
                raise PermanentProcessingError(f"image_id: {image_id} not found in DB")

            try:
                fetch_image = Image.open(Path(fetch_image_entity.origin_path))
            except FileNotFoundError as e:
                # 磁碟上實體檔案已不存在（可能被清理任務刪除），同樣是永久性失敗
                raise PermanentProcessingError(
                    f"image_id: {image_id}, file not found: {fetch_image_entity.origin_path}"
                ) from e


# === 寫入 image embedding info ===
# ======================================================================================================================
            fetch_image_embedding_entity = ImageEmbeddingService.get_image_embedding_metadata_by_image_id(
                image_id=fetch_image_entity.id,
                embedding_model=embedding_model,
            )

            if fetch_image_embedding_entity is None:
                fetch_embedding_res = ImageEmbeddingService.process_image_embedding(
                    EmbeddingRequest(
                        req_image=fetch_image,
                        embedding_model=embedding_model,
                    )
                )

                fetch_image_embedding_entity = ImageEmbeddingService.save_image_embedding_metadata(
                    ImageEmbeddingEntity(
                        image_id=fetch_image_entity.id,
                        model_name=embedding_model,
                        vector_512=fetch_embedding_res.image_embedding_vector
                    )
                )


# === 寫入所有 detect model info, 預先產出 cache ===
# ======================================================================================================================
            for detect_model in ImageConst.DETECT_MODELS:
                fetch_image_detection_entity = ImageDetectionService.get_image_detection_metadata_by_image_id(
                    image_id=fetch_image_entity.id,
                    detect_model=detect_model,
                )

                if fetch_image_detection_entity is None:
                    fetch_detect_res = ImageDetectionService.process_image_detection(
                        DetectionRequest(
                            req_image=fetch_image,
                            detect_model=detect_model,
                        )
                    )

                    fetch_detect_result = ImageProcessorService.save_image(
                        SaveImageRequest(
                            req_image=fetch_detect_res.detect_image,
                            category="thecatapi_detect_path",
                            file_name=fetch_image_entity.file_name,
                            sub_dir=detect_model,
                            convert_jpg=True,
                        )
                    )

                    fetch_image_detection_entity = (
                        ImageDetectionService.save_image_detection_metadata(
                            ImageDetectionEntity(
                                image_id=fetch_image_entity.id,
                                md5_hash=fetch_detect_result.md5,
                                detect_path=fetch_detect_result.path,
                                detect_model=detect_model,
                                predict_list=fetch_detect_res.predict_list,
                                tag_results=fetch_detect_res.tag_results,
                                has_cat=fetch_detect_res.has_cat,
                                is_preprocessed=True,
                            )
                        )
                    )


# === 寫入所有 transform model info, 預先產出 cache ===
# ======================================================================================================================
            for transform_model in ImageConst.TRANSFORM_MODELS:
                fetch_transform_entity = ImageTransformService.get_image_transform_metadata_by_image_id(
                    image_id=fetch_image_entity.id,
                    transform_model=transform_model,
                    style_ref_path=style_ref_path,
                    is_use=False
                )

                # 若 transform 圖片都已經使用過, 生成緩存
                if fetch_transform_entity is None:
                    fetch_transform_res = ImageTransformService.process_image_transform(
                        TransformRequest(
                            req_image=fetch_image,
                            transform_model=transform_model,
                            style_ref_path=style_ref_path
                        )
                    )

                    fetch_transform_result = ImageProcessorService.save_image(SaveImageRequest(
                        req_image=fetch_transform_res.transform_image,
                        category="thecatapi_transform_path",
                        file_name=fetch_image_entity.file_name,
                        sub_dir=transform_model,
                        convert_jpg=True
                    ))

                    fetch_transform_entity = ImageTransformService.save_image_transformation_metadata(
                        ImageTransformEntity(
                            image_id=fetch_image_entity.id,
                            md5_hash=fetch_transform_result.md5,
                            transform_path=fetch_transform_result.path,
                            transform_model=transform_model,
                            style_ref_path=style_ref_path,
                            is_use=False, # 未使用 flag
                            is_preprocessed=True,
                        )
                    )


#  === debug memory usage ===
# ======================================================================================================================
        log_device_memory(
            gpu_device,
            component="fetch_thecatapi_consumer_finished",
            stage="before_clear_cache",
            log_level=logging.DEBUG
        )

        clear_device_cache(gpu_device)

        log_device_memory(
            gpu_device,
            component="fetch_thecatapi_consumer_finished",
            stage="after_clear_cache",
            log_level=logging.DEBUG
        )

#  === GPU 降溫休息 ===
# ======================================================================================================================
        if gpu_rest_seconds > 0:
            logger.debug(f"image_id: {image_id}, GPU resting for {gpu_rest_seconds}s")
            time.sleep(gpu_rest_seconds)


        logger.debug(f"image_id: {image_id}, cost: {timer.costs.get(cost_id_str)}")



# return object
fetch_thecatapi_consumer = FetchThecatapiConsumer()