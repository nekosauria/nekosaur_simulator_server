import json
import threading
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from util.common import common
from util.step_timer import StepTimer
from util.rabbitmq import rabbitmq_batch_channel

logger = common.logger

T = TypeVar("T")


class PermanentProcessingError(Exception):
    """
    永久性失敗（重試也沒用的錯誤）。

    使用時機：資料本身有問題，不是暫時性故障，例如：
      - image_id 在 DB 裡查不到（資料已被刪除 / 從未存在）
      - 對應的實體檔案在磁碟上已經不存在（FileNotFoundError）
      - message payload 格式雖然能 parse，但欄位值明顯不合法（例如負數 id）

    子類別在 handle_message() 裡遇到這類狀況時，應該主動 raise 這個例外，
    而不是讓底層的 AttributeError / FileNotFoundError 等原生例外直接冒出去——
    因為 base class 會依例外型別決定要不要 requeue：

      - raise PermanentProcessingError → nack(requeue=False)
        訊息不會被丟回 queue，避免同一則壞資料被無限次重新消費、
        永遠卡在 queue 裡空轉、浪費運算資源（尤其這裡的 handle_message
        通常包含 GPU 推論，重試一次成本都不低）。

      - raise 其他一般 Exception（GPU OOM、DB 連線瞬斷、外部服務逾時等）
        → nack(requeue=True)
        這類錯誤有機會在下次重試時恢復，所以維持重新入隊。
    """
    pass


class BaseConsumer(ABC, Generic[T]):
    """
    RabbitMQ Consumer 共用基底類別。
    子類別只需要實作 queue_name / parse_payload / handle_message，
    connection、thread 生命週期、ack/nack、graceful shutdown 由這裡統一處理。
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
        """
        把原始 message body 轉成子類別要用的資料型別（例如 int image_id，或是自訂 dataclass）。
        parse 失敗時應該 raise Exception，base class 會統一處理成 nack(requeue=False)
        （壞掉的訊息格式屬於永久性錯誤，重試不會自己變好）。
        """
        raise NotImplementedError

    @abstractmethod
    def handle_message(self, payload: T, timer: StepTimer) -> None:
        """
        實際的業務處理邏輯（embedding / detection / transform 等）。

        - 遇到「資料本身有問題、重試也沒用」的狀況（查無此 id、檔案不存在等），
          請主動 raise PermanentProcessingError，讓訊息被丟棄而不是無限重新入隊。
        - 遇到「可能是暫時性」的狀況（GPU OOM、DB 瞬斷等），直接 raise 原生例外即可，
          base class 會自動 requeue 讓它有機會重試。
        """
        raise NotImplementedError



    # === 子類別可選擇覆寫 ===

    @property
    def prefetch_count(self) -> int:
        """一次最多同時處理幾則訊息，預設 1（GPU 任務建議維持 1）"""
        return 1

    # === Base class 共用邏輯，子類別不需要動 ===

    def _on_message(self, channel, method, properties, body):
        timer = StepTimer()

        # === 階段一：parse payload ===
        # parse 失敗（格式錯誤、缺欄位等）一律視為永久性錯誤，直接丟棄不 requeue，
        # 避免格式壞掉的訊息卡在 queue 裡無限循環。
        try:
            payload = self.parse_payload(body)
        except Exception as e:
            logger.error(f"[{self.queue_name}] Invalid message payload: {body}, error: {e}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        # === 階段二：實際業務處理 ===
        try:
            self.handle_message(payload, timer)
            channel.basic_ack(delivery_tag=method.delivery_tag)

        except PermanentProcessingError as e:
            # 資料本身有問題（查無此紀錄、檔案遺失等），重試也不會成功，
            # 直接丟棄，避免無限重新入隊、無限重跑消耗 GPU 資源。
            # TODO: 未來若要接 DLQ（死信佇列），改成 publish 到 {queue_name}.dlq 再 nack，
            # 方便事後排查是哪些資料出了問題，而不是直接消失不留痕跡。
            logger.error(
                f"[{self.queue_name}] Permanent failure, discard message. "
                f"payload: {payload}, error: {e}"
            )
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        except Exception as e:
            # 未預期的例外，視為暫時性錯誤（GPU OOM、DB 連線瞬斷、外部服務逾時等），
            # 重新丟回 queue 讓下次還有機會處理成功。
            logger.error(
                f"[{self.queue_name}] Failed to process payload: {payload}, error: {e}",
                exc_info=True,
            )
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

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
        """在背景 thread 啟動 consumer，不阻塞 Flask 主 thread"""
        self._thread = threading.Thread(
            target=self._run, daemon=True, name=f"rabbitmq-consumer-{self.queue_name}"
        )
        self._thread.start()

    def stop(self):
        """從 Flask app 關閉時呼叫，讓 consumer thread 優雅退出"""
        if self._channel is not None and self._channel.is_open:
            self._channel.connection.add_callback_threadsafe(self._channel.stop_consuming)
        self._stopped.wait(timeout=10)