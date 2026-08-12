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

from entity.image import Image as ImageEntity
from entity.image_detection import ImageDetection as ImageDetectionEntity
from entity.image_transform import ImageTransform as ImageTransformEntity
from entity.image_embedding import ImageEmbedding as ImageEmbeddingEntity
from util.device import log_device_memory, clear_device_cache, get_gpu_device

from util.step_timer import StepTimer

logger = common.logger
config = common.config
gpu_device = get_gpu_device()
embedding_model = ImageConst.MODEL_CLIP_VIT_B_32
style_ref_path = config.get('image', "default_style_ref_path")


if __name__ == "__main__":
    ...

# # === TODO rabbit mq consumer ===
# # start rabbitmq consumer
# # ======================================================================================================================
#     timer = StepTimer()
#
#
# # 開始跑 consumer 接收到的批次任務
# # ======================================================================================================================
#     with timer.track("fetch_thecatapi_consumer_total_cost"):
#         fetch_thecatapi_image_count = [3,2,5,1,4]
#
#         for index in fetch_thecatapi_image_count:
#             image_id = fetch_thecatapi_image_count[index]
#             cost_id_str = f"index: {index}, image_id: {image_id}, fetch_thecatapi_consumer_cost"
#             with timer.track(cost_id_str):
#
# # 執行單筆任務
# # ======================================================================================================================
#                 #  === 取得 fetch image entity ===
#                 fetch_image_entity = ImageService.get_image_metadata_by_id(image_id)
#                 fetch_image = Image.open(Path(fetch_image_entity.origin_path))
#
#
#                 #  === 寫入 fetch image_embedding info ===
#                 # 檢查是否已有 image_embedding info
#                 fetch_image_embedding_entity = ImageEmbeddingService.get_image_embedding_metadata_by_image_id(
#                     image_id=fetch_image_entity.id,
#                     embedding_model=embedding_model,
#                 )
#
#                 # 沒有則寫入
#                 if fetch_image_embedding_entity is None:
#                     # get fetch image_embedding vector
#                     fetch_embedding_res = ImageEmbeddingService.process_image_embedding(
#                         EmbeddingRequest(
#                             req_image=fetch_image,
#                             embedding_model=embedding_model,
#                         )
#                     )
#
#                     # save fetch image_embedding metadata
#                     fetch_image_embedding_entity = ImageEmbeddingService.save_image_embedding_metadata(
#                         ImageEmbeddingEntity(
#                             image_id=fetch_image_entity.id,
#                             model_name=embedding_model,
#                             vector_512=fetch_embedding_res.image_embedding_vector
#                         )
#                     )
#
#
#                 #  === 寫入 fetch detect info ===
#                 for detect_model in ImageConst.DETECT_MODELS:
#                     # 檢查是否已有 detection info
#                     fetch_image_detection_entity = ImageDetectionService.get_image_detection_metadata_by_image_id(
#                         image_id=fetch_image_entity.id,
#                         detect_model=detect_model,
#                     )
#
#                     # 沒有則寫入
#                     if fetch_image_detection_entity is None:
#                         # draw predict detect image
#                         fetch_detect_res = ImageDetectionService.process_image_detection(
#                             DetectionRequest(
#                                 req_image=fetch_image,
#                                 detect_model=detect_model,
#                             )
#                         )
#
#                         # save fetch detect image
#                         fetch_detect_result = ImageProcessorService.save_image(
#                             SaveImageRequest(
#                                 req_image=fetch_detect_res.detect_image,
#                                 category="thecatapi_detect_path",
#                                 file_name=fetch_image.filename,
#                                 sub_dir=detect_model,
#                                 convert_jpg=True,
#                             )
#                         )
#
#                         # save fetch image_detection metadata
#                         fetch_image_detection_entity = (
#                             ImageDetectionService.save_image_detection_metadata(
#                                 ImageDetectionEntity(
#                                     image_id=fetch_image_entity.id,
#                                     md5_hash=fetch_detect_result.md5,
#                                     detect_path=fetch_detect_result.path,
#                                     detect_model=detect_model,
#                                     predict_list=fetch_detect_res.predict_list,
#                                     tag_results=fetch_detect_res.tag_results,
#                                     has_cat=fetch_detect_res.has_cat,
#                                     is_preprocessed=True,
#                                 )
#                             )
#                         )
#
#
#                 #  === 寫入 transform info ===
#                 for transform_model in ImageConst.TRANSFORM_MODELS:
#                     # 檢查是否已有 transform info 的 cache
#                     fetch_transform_entity = ImageTransformService.get_image_transform_metadata_by_image_id(
#                         image_id=fetch_image_entity.id,
#                         transform_model=transform_model,
#                         style_ref_path=style_ref_path,
#                     )
#
#                     # 沒有則寫入
#                     if fetch_transform_entity is None:
#                         # 風格轉換圖生成
#                         fetch_transform_res = ImageTransformService.process_image_transform(
#                             TransformRequest(
#                                 req_image=fetch_image,
#                                 transform_model=transform_model,
#                                 style_ref_path=style_ref_path
#                             )
#                         )
#
#                         # 下載圖片
#                         fetch_transform_result = ImageProcessorService.save_image(SaveImageRequest(
#                             req_image=fetch_transform_res.transform_image,
#                             category="thecatapi_transform_path",
#                             file_name=fetch_image.filename,
#                             sub_dir=transform_model,
#                             convert_jpg=True
#                         ))
#
#                         # save image_transform metadata
#                         origin_transform_entity = ImageTransformService.save_image_transformation_metadata(
#                             ImageTransformEntity(
#                                 image_id=fetch_image_entity.id,
#                                 md5_hash=fetch_transform_result.md5,
#                                 transform_path=fetch_transform_result.path,
#                                 transform_model=transform_model,
#                                 style_ref_path=style_ref_path,
#                                 is_use=True,
#                                 is_preprocessed=True,
#                             )
#                         )
#
#
# #  === debug memory usage ===
# # ======================================================================================================================
#                 # 清理前
#                 log_device_memory(
#                     gpu_device,
#                     component="flask_upload_api_finished",
#                     stage="before_clear_cache",
#                     log_level=logging.DEBUG
#                 )
#
#                 # 一個週期完成後，清理 PyTorch 顯存快取
#                 clear_device_cache(gpu_device)
#
#                 # 清理後
#                 log_device_memory(
#                     gpu_device,
#                     component="flask_upload_api_finished",
#                     stage="after_clear_cache",
#                     log_level=logging.DEBUG
#                 )
#
#
#
#             # 計算 cost time
# # ======================================================================================================================
#
#             logger.debug(f"image_id: {image_id}, fetch_thecatapi_consumer_cost: {timer.costs.get(cost_id_str)}")
#
#     logger.debug(f"fetch_thecatapi_consumer_total_cost: {timer.costs.get("fetch_thecatapi_consumer_total_cost")}")

