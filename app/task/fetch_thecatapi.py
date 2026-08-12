import requests

from util.common import common
from entity.image import Image

from dto.image_processor import SaveImageRequest

from service.image import Image as ImageService
from service.image_processor import ImageProcessor as ImageProcessorService

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

            # push to rabbitmq producer

        # 紀錄 cost time
        logger.info(timer.costs.get("trigger_fetch_thecatapi_task_cost"))