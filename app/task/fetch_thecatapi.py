import json
import pika
import requests

from const.image_const import ImageConst
from service.image import Image as ImageService
from util.common import common
from util.image import compute_image_md5, url_to_pil_image
from util.rabbitmq import rabbitmq_batch_channel
from util.step_timer import StepTimer

# 取得 config 與 logger
config = common.config
logger = common.logger

# 讀取 task & rabbitmq 相關設定
request_url = config.get('task', "thecatapi_url") + config.get('task', "thecatapi_key")
fetch_queue_name = config.get("rabbitmq", "fetch_thecatapi_queue_name")
fetch_count = int(config.get('task', 'fetch_thecatapi_count'))


def fetch_thecatapi_url() -> dict:
    """發送 HTTP 請求向 TheCatAPI 取得圖片資訊"""
    # 加入 timeout 避免網路異常導致無期限 hang 住
    response = requests.get(request_url, timeout=10)
    response.raise_for_status()
    fetch_data = response.json()

    logger.debug(f"fetch_data: {fetch_data}")
    return fetch_data


def trigger():
    """觸發抓取 TheCatAPI 圖片的批次任務並推送到 RabbitMQ"""
    timer = StepTimer()

    # 任務計時 cost time
    with timer.track("trigger_fetch_thecatapi_task_cost"):
        # 開一次連線，整個 batch 共用
        with rabbitmq_batch_channel(fetch_queue_name) as ch:
            # 跑批次迴圈
            for i in range(fetch_count):
                try:
                    # === 取得 fetch thecatapi data 與下載圖片 ===
                    logger.debug(f"Download image {i + 1}/{fetch_count}")
                    fetch_data = fetch_thecatapi_url()
                    item_data = fetch_data[0]
                    fetch_image_url = item_data["url"]
                    logger.debug(f"fetch_image_url: {fetch_image_url}")

                    fetch_img, fetch_img_name = url_to_pil_image(fetch_image_url)

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
                        continue  # 發現重複直接跳過

                    # === 原圖處理與存檔 ===
                    fetch_image_entity = ImageService.save_and_insert_image(
                        req_image=fetch_img,
                        file_name=fetch_img_name,
                        save_category=ImageConst.THECATAPI_ORIGIN_PATH,
                        image_source=ImageConst.THECATAPI_IMAGE_SOURCE,
                        raw_source=item_data,
                    )

                    logger.debug(f"image_id: {fetch_image_entity.id}")

                    # === Push to RabbitMQ Producer ===
                    ch.basic_publish(
                        exchange="",
                        routing_key=fetch_queue_name,
                        body=json.dumps(
                            {"image_id": fetch_image_entity.id},
                            ensure_ascii=False,
                        ).encode("utf-8"),
                        properties=pika.BasicProperties(
                            delivery_mode=pika.DeliveryMode.Persistent
                        ),
                    )

                except Exception as e:
                    # 個別任務失敗印出 log 後繼續執行下一筆，不打斷整體批次
                    logger.error(
                        f"[{i + 1}/{fetch_count}] Fetch TheCatAPI process failed: {e}",
                        exc_info=True,
                    )

        # 紀錄總 cost time
        logger.info(timer.costs.get("trigger_fetch_thecatapi_task_cost"))