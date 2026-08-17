import threading
import time
from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from pathlib import Path

from PIL import Image
import pika

from util.common import common
from util.step_timer import StepTimer
from util.rabbitmq import rabbitmq_batch_channel

from service.image import Image as ImageService
from util.torch_util import clear_device_cache_with_log

logger = common.logger

T = TypeVar("T")


class PermanentProcessingError(Exception):
    """
    永久性失敗（重試也沒用的錯誤）。
    """
    pass


class BaseImageConsumer(ABC, Generic[T]):
    """
    RabbitMQ Consumer 共用基底類別。
    支援『重試上限』機制，避免暫時性錯誤導致 Queue 無限循環卡死。
    """

    def __init__(self):
        self._channel = None
        self._thread = None
        self._stopped = threading.Event()


    # === 子類別必須實作 ===

    @property
    @abstractmethod
    def queue_name(self) -> str:
        """這個 consumer 要監聽的 queue 名稱"""
        raise NotImplementedError

    @abstractmethod
    def parse_payload(self, body: bytes) -> T:
        raise NotImplementedError

    @abstractmethod
    def handle_message(self, payload: T, timer: StepTimer) -> None:
        raise NotImplementedError

    # === 子類別可選擇覆寫 ===

    @property
    def prefetch_count(self) -> int:
        """一次最多同時處理幾則訊息，預設 1（GPU 任務建議維持 1）"""
        return 1

    @property
    def max_retries(self) -> int:
        """最大重試次數，預設 3 次（超過則視為永久失敗並丟棄）"""
        return 3


    # === 工具方法 ===

    @staticmethod
    def _load_image_or_raise(image_id: int):
        image_entity = ImageService.get_image_metadata_by_id(image_id)

        if image_entity is None:
            raise PermanentProcessingError(
                f"image_id={image_id} not found in DB"
            )

        try:
            image = Image.open(
                Path(image_entity.origin_path)
            )
        except FileNotFoundError as e:
            raise PermanentProcessingError(
                f"image_id={image_id}, "
                f"file not found: {image_entity.origin_path}"
            ) from e

        return image_entity, image

    @staticmethod
    def _finish(
            image_id: int,
            timer: StepTimer,
            cost_id: str,
            gpu_device,
            gpu_rest_seconds: float = 0,
            component: str = "base_consumer_finished",
    ) -> None:
        clear_device_cache_with_log(
            gpu_device,
            component=component,
        )

        if gpu_rest_seconds > 0:
            logger.debug(
                f"image_id={image_id}, "
                f"GPU resting for {gpu_rest_seconds}s"
            )
            time.sleep(gpu_rest_seconds)

        logger.debug(
            f"image_id={image_id}, "
            f"cost={timer.costs.get(cost_id)}"
        )

    def _requeue_with_retry_count(self, channel, method, properties, body, current_retry_count: int):
        """
        重新發送訊息並手動將 x-retry-count + 1
        """
        headers = properties.headers or {}
        headers["x-retry-count"] = current_retry_count + 1

        new_properties = pika.BasicProperties(
            headers=headers,
            delivery_mode=properties.delivery_mode or 2,  # 預設維持持久化
            content_type=properties.content_type,
        )

        # 重新寫回原 Queue
        channel.basic_publish(
            exchange="",
            routing_key=self.queue_name,
            body=body,
            properties=new_properties,
        )
        # 確認 ACK 掉當前舊訊息（已生成新訊息替代）
        channel.basic_ack(delivery_tag=method.delivery_tag)


    # === Base class 共用邏輯 ===

    def _on_message(self, channel, method, properties, body):
        timer = StepTimer()

        # === 階段一：parse payload ===
        try:
            payload = self.parse_payload(body)
        except Exception as e:
            logger.error(f"[{self.queue_name}] Invalid message payload: {body}, error: {e}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        # === 階段二：讀取目前已重試次數 ===
        headers = properties.headers or {}
        retry_count = headers.get("x-retry-count", 0)

        # === 階段三：實際業務處理 ===
        try:
            self.handle_message(payload, timer)
            channel.basic_ack(delivery_tag=method.delivery_tag)

        except PermanentProcessingError as e:
            # 資料本身有問題，直接丟棄不重試
            logger.error(
                f"[{self.queue_name}] Permanent failure, discard message. "
                f"payload: {payload}, error: {e}"
            )
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        except Exception as e:
            # 未預期的例外（GPU OOM、DB 瞬斷等）
            if retry_count < self.max_retries:
                logger.errors(
                    f"[{self.queue_name}] Failed to process payload (Retry {retry_count + 1}/{self.max_retries}): "
                    f"payload: {payload}, error: {e}"
                )
                # 重新發送帶有更新後重試次數的訊息
                self._requeue_with_retry_count(channel, method, properties, body, retry_count)
            else:
                # 超過最大重試次數，不再入隊
                logger.error(
                    f"[{self.queue_name}] Exceeded max retries ({self.max_retries}), discarding message. "
                    f"payload: {payload}, error: {e}",
                    exc_info=True,
                )
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def _run(self):
        with rabbitmq_batch_channel(self.queue_name) as ch:
            self._channel = ch
            ch.basic_qos(prefetch_count=self.prefetch_count)
            ch.basic_consume(
                queue=self.queue_name,
                on_message_callback=self._on_message,
                auto_ack=False,
            )
            logger.info(f"Start consuming queue: {self.queue_name}")

            try:
                ch.start_consuming()
            except Exception as e:
                logger.error(f"[{self.queue_name}] Consumer thread crashed: {e}", exc_info=True)
            finally:
                self._stopped.set()
                logger.info(f"[{self.queue_name}] Consumer thread stopped")

    def start(self):
        """在背景 thread 啟動 consumer"""
        self._thread = threading.Thread(
            target=self._run, daemon=True, name=f"rabbitmq-consumer-{self.queue_name}"
        )
        self._thread.start()

    def stop(self):
        """優雅退出"""
        if self._channel is not None and self._channel.is_open:
            self._channel.connection.add_callback_threadsafe(self._channel.stop_consuming)
        self._stopped.wait(timeout=10)