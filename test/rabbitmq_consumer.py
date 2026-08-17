import json
import time
import traceback
from util.rabbitmq import rabbitmq_channel


def process_task_slowly(data: dict):
    """模擬耗時工作或限制消化速度"""
    task_id = data.get("task_id")
    print(f"     [⚙️  開始處理 Task: {task_id}]")

    # 關鍵：用 sleep 模擬耗時操作，或主動限制處理速度（例如每秒最多處理 N 筆）
    time.sleep(2)  # 慢慢消化：每筆強制花 2 秒

    print(f"     [✓] Task {task_id} 處理完成了！")


def callback(ch, method, properties, body):
    try:
        data = json.loads(body.decode("utf-8"))
        print(f"\n [✓] 從 Queue 拿取 1 則 Task: {data.get('task_id')}")

        # 執行消化邏輯 (內含 time.sleep)
        process_task_slowly(data)

        # 處理完成後才送出 ACK，此時 RabbitMQ 才會再發下一筆過來
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f" [!] 訊息處理失敗: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def start_consumer(queue_name: str = "rabbitmq_test_queue"):
    with rabbitmq_channel() as channel:
        channel.queue_declare(queue=queue_name, durable=True)

        # ⭐️ 最關鍵這行：設定 prefetch_count=1 (一次只拿一筆，沒 ACK 前不准再發)
        channel.basic_qos(prefetch_count=1)

        channel.basic_consume(
            queue=queue_name, on_message_callback=callback, auto_ack=False
        )

        print(f" [*] Daemon 啟動中，開始慢慢消化 Queue...")
        channel.start_consuming()


if __name__ == "__main__":
    start_consumer()