import argparse
from datetime import datetime, timezone
import random
import time
import uuid
from util.rabbitmq import send_rabbitmq_message


def send_batch_messages(count: int = 5, delay: float = 0.2):
    """
    批量發送 RabbitMQ 測試訊息

    :param count: 要發送的訊息筆數
    :param delay: 每筆訊息之間的間隔秒數 (避免瞬間大量打入，方便觀測)
    """
    # 使用 Unsplash 真實可讀取的貓咪圖片網址
    sample_images = [
        "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba",
        "https://images.unsplash.com/photo-1573865526739-10659fec78a5",
        "https://images.unsplash.com/photo-1533738363-b7f9aef128ce",
        "https://images.unsplash.com/photo-1495360010541-f48722b34f7d",
    ]
    sample_events = ["process_cat_image", "resize_cat_avatar", "detect_cat_face"]

    queue_name = "rabbitmq_test_queue"
    print(f"🚀 開始發送 {count} 筆測試訊息至佇列 '{queue_name}'...\n")

    for i in range(1, count + 1):
        payload = {
            "task_id": str(uuid.uuid4()),  # 隨機生成唯一識別碼 (UUIDv4)
            "event": random.choice(sample_events),  # 隨機事件名稱
            "image_url": random.choice(sample_images),  # 隨機真實圖片網址
            "priority": random.randint(1, 5),  # 隨機優先級 (1~5)
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),  # UTC 時間戳記
        }

        # 發送訊息
        send_rabbitmq_message(queue_name, payload)

        print(
            f"  [{i}/{count}] 送出 Task ID: {payload['task_id']} ({payload['event']})"
        )

        if delay > 0 and i < count:
            time.sleep(delay)

    print(f"\n✅ 成功完成 {count} 筆訊息的發送！")


if __name__ == "__main__":
    # 可以透過命令行指定數量，例如: python producer.py -n 10
    parser = argparse.ArgumentParser(description="Batch publish test messages to RabbitMQ")

    send_batch_messages(count=10, delay=2.0)