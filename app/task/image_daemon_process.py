# daemon/image_daemon_process.py
from datetime import datetime, timedelta

from util.common import common
from service.image import Image as ImageService
from util.image import check_file_exists
from util.step_timer import StepTimer
from util.rabbitmq import rabbitmq_batch_channel

import json
import pika


# get conf
config = common.config
logger = common.logger

# daemon 只處理 created_at 落在 [after_cutoff, before_cutoff] 區間內的 image
# 太新的圖片還在走 fetch → consumer 的正常 pipeline，不該被 daemon 插手
# 太舊的圖片（超出保存期限/防呆）也不需要再檢查
check_after_days = int(config.get('task', 'image_daemon_process_check_after_days'))
check_before_days = int(config.get('task', 'image_daemon_process_check_before_days'))
batch_size = int(config.get('task', 'image_daemon_process_batch_size'))

daemon_queue_name = config.get("rabbitmq", "image_daemon_process_queue_name")


def check_and_soft_delete_missing_origin(image_entity) -> bool:
    """
    Step 2: 檢查原圖 origin_path 實體檔案是否存在，不存在則 soft delete image。
    :return: False 代表原圖已遺失（已 soft delete），呼叫端應該跳過該筆，不發送到 queue。
    """
    if check_file_exists(image_entity.origin_path):
        return True
    else:
        logger.info(
            f"image_id: {image_entity.id}, origin file missing: {image_entity.origin_path}, soft delete"
        )
        ImageService.soft_delete_image(image_entity.id)
        return False



def trigger():
    timer = StepTimer()

    with timer.track("image_daemon_process_trigger_cost"):

        # 檢查區間：不要太新（還在 pipeline 中）、也不要太舊（超出保存期限/防呆）
        before_cutoff = datetime.now() - timedelta(days=check_before_days)
        after_cutoff = datetime.now() - timedelta(days=check_after_days)

        logger.info(
            f"image_daemon_process trigger, "
            f"created_at range: [{after_cutoff}, {before_cutoff}], batch_size: {batch_size}"
        )

        # === 撈出 created_at 落在區間內的 image（分批）===
        # ======================================================================================================================
        image_entities = ImageService.get_images_created_between(
            after=after_cutoff,
            before=before_cutoff,
            limit=batch_size,
        )
        logger.info(f"image_daemon_process, found {len(image_entities)} images to check (this batch)")

        # 開一次連線，整個 batch 共用
        with rabbitmq_batch_channel(daemon_queue_name) as ch:

            for image_entity in image_entities:
                try:
                    # === 原圖是否遺失（不需要 model，daemon 自己就能做完）===
                    # ======================================================================================================================
                    if not check_and_soft_delete_missing_origin(image_entity):
                        logger.debug(f"image_id: {image_entity.id}, origin missing, skip publish")
                        continue

                    # === push to rabbitmq producer，交給 consumer 做剩下需要 model 的步驟 ===
                    # ======================================================================================================================
                    ch.basic_publish(
                        exchange="",
                        routing_key=daemon_queue_name,
                        body=json.dumps(
                            {"image_id": image_entity.id},
                            ensure_ascii=False,
                        ).encode("utf-8"),
                        properties=pika.BasicProperties(
                            delivery_mode=pika.DeliveryMode.Persistent
                        ),
                    )

                except Exception as e:
                    # 單筆失敗不應該讓整批 daemon 掛掉，記錄後繼續處理下一筆
                    logger.error(
                        f"image_id: {image_entity.id}, image_daemon_process trigger failed: {e}",
                        exc_info=True,
                    )

    logger.info(timer.costs.get("image_daemon_process_trigger_cost"))


if __name__ == "__main__":
    trigger()