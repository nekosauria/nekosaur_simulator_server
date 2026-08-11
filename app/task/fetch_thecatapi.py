import requests

from const.image_const import ImageConst
from dto.image_processor import SaveImageRequest
from util.common import common
from entity.image import Image

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

from util.image import download_image
from util.step_timer import StepTimer

# get conf
config = common.config
logger = common.logger

request_url = config.get('task', "thecatapi_url") + config.get('task', "thecatapi_key")

def fetch_thecatapi_url() -> dict:
    # fetch thecatapi
    response = requests.get( request_url )

    response.raise_for_status()
    fetch_data = response.json()

    logger.debug(f"fetch_data: {fetch_data}")

    return fetch_data


def trigger():
    timer = StepTimer()

    # 任務計時 cost time
    with timer.track("trigger_fetch_thecatapi_task_cost"):

        # === 取參數 ===
        count = int(config.get('task', 'fetch_thecatapi_count'))
        embedding_model = config.get("model", "clip_vit_b_32_model_path")

        # 跑批次迴圈
        for i in range(count):
            # === 取得 fetch thecatapi data ===
            logger.debug(f"Download image {i + 1}/{count}")
            fetch_data = fetch_thecatapi_url()
            fetch_image_url = fetch_data[0]["url"]
            logger.debug(f"fetch_image_url: {fetch_image_url}")

            fetch_img, fetch_img_name = download_image(fetch_image_url)


            #  === 原圖處理 ===
            # save fetch image
            fetch_res = ImageProcessorService.save_image(SaveImageRequest(
                req_image=fetch_img,
                category="thecatapi_origin_path",
                file_name=fetch_img_name,
                sub_dir=None,
                convert_jpg=False,
            ))
            logger.debug(f"Saved to: {fetch_res.path}")

            # save fetch image metadata
            fetch_image_entity = ImageService.save_image_metadata(
                Image(
                    md5_hash=fetch_res.md5,
                    origin_path=fetch_res.path,
                    image_source=config.get('task', "thecatapi_url"),
                    raw_source=fetch_data
                )
            )
            logger.debug(f"image_id: {fetch_image_entity.id}")


# === TODO rabbit mq ===
# ======================================================================================================================
#             #  === 寫入 fetch image_embedding info ===
#             # get fetch image_embedding vector
#             fetch_embedding_res = ImageEmbeddingService.process_image_embedding(
#                 EmbeddingRequest(
#                     req_image=fetch_img,
#                     embedding_model=embedding_model,
#                 )
#             )
#
#
#             # save fetch image_embedding metadata
#             fetch_image_embedding_entity = ImageEmbeddingService.save_image_embedding_metadata(
#                 ImageEmbeddingEntity(
#                     image_id=fetch_image_entity.id,
#                     model_name=embedding_model,
#                     vector_512=fetch_embedding_res.image_embedding_vector
#                 )
#             )
#
#             #  === 寫入 fetch detect info ===
#             for detect_model in ImageConst.DETECT_MODELS:
#                 # draw predict detect image
#                 fetch_detect_res = ImageDetectionService.process_image_detection(
#                     DetectionRequest(
#                         req_image=fetch_img,
#                         detect_model=detect_model,
#                     )
#                 )
#
#                 # save fetch detect image
#                 fetch_detect_result = ImageProcessorService.save_image(
#                     SaveImageRequest(
#                         req_image=fetch_detect_res.detect_image,
#                         category="user_upload_detect_path",
#                         file_name=fetch_img_name,
#                         sub_dir=detect_model,
#                         convert_jpg=True,
#                     )
#                 )
#
#                 # save fetch image_detection metadata
#                 fetch_image_detection_entity = (
#                     ImageDetectionService.save_image_detection_metadata(
#                         ImageDetectionEntity(
#                             image_id=fetch_image_entity.id,
#                             md5_hash=fetch_detect_result.md5,
#                             detect_path=fetch_detect_result.path,
#                             detect_model=detect_model,
#                             predict_list=fetch_detect_res.predict_list,
#                             tag_results=fetch_detect_res.tag_results,
#                         )
#                     )
#                 )
#
#
#             #  === 寫入 transform info ===
#             for transform_model in ImageConst.TRANSFORM_MODELS:
#                 # 風格轉換圖生成
#                 fetch_transform_res = ImageTransformService.process_image_transform(
#                     TransformRequest(
#                         req_image=fetch_img,
#                         transform_model=transform_model,
#                         style_ref_image= config.get('image', "default_style_ref_img")
#                     )
#                 )
#
#                 # 下載圖片
#                 fetch_transform_result = ImageProcessorService.save_image(SaveImageRequest(
#                     req_image=fetch_transform_res.transform_image,
#                     category="user_upload_transform_path",
#                     file_name=fetch_img_name,
#                     sub_dir=transform_model,
#                     convert_jpg=True
#                 ))
#
#                 # save image_transform metadata
#                 origin_transform_entity = ImageTransformService.save_image_transformation_metadata(
#                     ImageTransformEntity(
#                         image_id=fetch_image_entity.id,
#                         md5_hash=fetch_transform_result.md5,
#                         transform_path=fetch_transform_result.path,
#                         transform_model=transform_model,
#                     )
#                 )

        # 紀錄 cost time
        logger.info(timer.costs.get("trigger_fetch_thecatapi_task_cost"))