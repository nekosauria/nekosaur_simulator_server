import requests

from util.common import common

from dto.image_processor import SaveImageRequest

from service.image import Image as ImageService
from service.image_processor import ImageProcessor as ImageProcessorService

from entity.image import Image as ImageEntity

from util.image import download_image, compute_image_md5
from util.step_timer import StepTimer
from util.rabbitmq import rabbitmq_batch_channel

import json
import pika


# get conf
config = common.config
logger = common.logger

thecatapi_url = config.get('task', "thecatapi_url")
request_url = config.get('task', "thecatapi_url") + config.get('task', "thecatapi_key")
web_dns_url = config.get("server", "web_dns_url")
upload_prefix = config.get("api", "nekosaur_server_upload_prefix")
fetch_queue_name = config.get("rabbitmq", "fetch_thecatapi_queue_name")


def fetch_thecatapi_url() -> dict:
    # fetch thecatapi
    response = requests.get(request_url)

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

        # 開一次連線，整個 batch 共用
        with rabbitmq_batch_channel(fetch_queue_name) as ch:

            # 跑批次迴圈
            for i in range(count):
                # === 取得 fetch thecatapi data ===
                logger.debug(f"Download image {i + 1}/{count}")
                fetch_data = fetch_thecatapi_url()
                fetch_image_url = fetch_data[0]["url"]
                logger.debug(f"fetch_image_url: {fetch_image_url}")

                fetch_img, fetch_img_name = download_image(fetch_image_url)


                # === 檢查是否已有 image info（MD5 去重）===
                fetch_img_md5 = compute_image_md5(
                    image=fetch_img,
                    file_name=fetch_img_name,
                    convert_jpg=False,
                )

                origin_image_entity = ImageService.get_image_metadata_by_md5_hash(
                    md5_hash=fetch_img_md5
                )

                if origin_image_entity is not None:
                    logger.info(
                        f"Duplicate image detected (md5: {fetch_img_md5}), "
                        f"skip insert & publish, existing image_id: {origin_image_entity.id}"
                    )
                    continue


                #  === 原圖處理 ===
                # save fetch image
                fetch_result = ImageProcessorService.save_image(SaveImageRequest(
                    req_image=fetch_img,
                    category="thecatapi_origin_path",
                    file_name=fetch_img_name,
                    sub_dir=None,
                    convert_jpg=False,
                ))
                logger.debug(f"Saved to: {fetch_result.path}")

                # save fetch image metadata
                fetch_image_entity = ImageService.insert_image_metadata(
                    ImageEntity(
                        md5_hash=fetch_result.md5,
                        origin_path=fetch_result.path,
                        image_source=thecatapi_url,
                        file_name = fetch_img_name,
                        raw_source=fetch_data,
                        is_deleted=False
                    )
                )

                logger.debug(f"image_id: {fetch_image_entity.id}")


                #  === push to rabbitmq producer ===
                ch.basic_publish(
                    exchange="",
                    routing_key=fetch_queue_name,
                    body=json.dumps(
                        {
                            "image_id": fetch_image_entity.id,
                        },
                        ensure_ascii=False,
                    ).encode("utf-8"),
                    properties=pika.BasicProperties(
                        delivery_mode=pika.DeliveryMode.Persistent
                    ),
                )

        # 紀錄 cost time
        logger.info(timer.costs.get("trigger_fetch_thecatapi_task_cost"))