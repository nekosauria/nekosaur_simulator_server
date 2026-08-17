import json

from const.image_const import ImageConst
from util.common import common

from service.image import Image as ImageService
from service.image_detection import ImageDetection as ImageDetectionService
from service.image_transform import ImageTransform as ImageTransformService
from service.image_embedding import ImageEmbedding as ImageEmbeddingService

from util.torch_util import get_gpu_device
from util.step_timer import StepTimer

from worker.base_image_consumer import BaseImageConsumer

logger = common.logger
config = common.config
gpu_device = get_gpu_device()
embedding_model = ImageConst.MODEL_CLIP_VIT_B_32
style_ref_path = config.get('image', "default_style_ref_path")

# GPU 降溫休息秒數，每處理完一筆訊息後 sleep ，避免連續高負載導致過熱/降頻
gpu_rest_seconds = float(config.get("rabbitmq", "fetch_thecatapi_consumer_rest_time"))


class FetchThecatapiConsumer(BaseImageConsumer[int]): # int = 這個 consumer 的訊息解析完後長什麼樣子

    @property
    def queue_name(self) -> str:
        return config.get("rabbitmq", "fetch_thecatapi_queue_name")

    @property
    def prefetch_count(self) -> int:
        return 1

    @property
    def max_retries(self) -> int:
        return 2

    def parse_payload(self, body: bytes) -> int:
        payload = json.loads(body.decode("utf-8"))
        return payload["image_id"]

    def handle_message(self, image_id: int, timer: StepTimer) -> None:
        cost_id_str = f"image_id: {image_id}, fetch_thecatapi_consumer_cost"

        with timer.track(cost_id_str):

# === 取得 image entity + 原圖（含永久性失敗檢查）===
# ======================================================================================================================
            fetch_image_entity, fetch_image = self._load_image_or_raise(
                image_id
            )

# === 寫入 image embedding info ===
# ======================================================================================================================
            fetch_image_embedding_entity = ImageEmbeddingService.get_or_generate_embedding(
                image_entity=fetch_image_entity,
                req_image=fetch_image,
                embedding_model=embedding_model,
            )


# === 寫入所有 detect model info, 預先產出 cache ===
# ======================================================================================================================
            for detect_model in ImageConst.DETECT_MODELS:
                fetch_image_detection_entity = ImageDetectionService.get_or_generate_detection(
                    image_entity=fetch_image_entity,
                    req_image=fetch_image,
                    detect_model=detect_model,
                    save_category=ImageConst.THECATAPI_DETECT_PATH,
                    is_preprocessed=True,
                )


# === 寫入所有 transform model info, 預先產出 cache ===
# ======================================================================================================================
            for transform_model in ImageConst.TRANSFORM_MODELS:
                fetch_transform_entity = ImageTransformService.get_or_generate_transform(
                    image_entity=fetch_image_entity,
                    req_image=fetch_image,
                    transform_model=transform_model,
                    style_ref_path=style_ref_path,
                    save_category=ImageConst.THECATAPI_TRANSFORM_PATH,
                    is_use=False,
                    is_preprocessed=True,
                )


# === 更新 image last_checked_at ===
# ======================================================================================================================
            ImageService.update_last_checked_at(
                image_id=fetch_image_entity.id,
            )


# === clear & debug memory usage ===
# ======================================================================================================================
        self._finish(
            image_id=image_id,
            timer=timer,
            cost_id=cost_id_str,
            gpu_device=gpu_device,
            gpu_rest_seconds=gpu_rest_seconds,
            component="fetch_thecatapi_consumer_finished",
        )



# return object
fetch_thecatapi_consumer = FetchThecatapiConsumer()