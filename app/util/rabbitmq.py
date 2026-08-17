from contextlib import contextmanager
import json
import pika
from util.common import common

config = common.config

# 讀取設定
HOST = config.get("rabbitmq", "host")
PORT = int(config.get("rabbitmq", "port"))
USER = config.get("rabbitmq", "user")
PASS = config.get("rabbitmq", "password")
VHOST = config.get("rabbitmq", "vhost")


def get_rabbitmq_connection() -> pika.BlockingConnection:
    credentials = pika.PlainCredentials(USER, PASS)
    parameters = pika.ConnectionParameters(
        host=HOST,
        port=PORT,
        virtual_host=VHOST,
        credentials=credentials,
        heartbeat=60,
    )
    return pika.BlockingConnection(parameters)


@contextmanager
def rabbitmq_channel():
    """
    提供 Flask 使用的 Channel contextmanager。
    Flask 每個 Request 借用一個連線與 Channel，用完自動關閉。
    """
    conn = get_rabbitmq_connection()
    channel = conn.channel()
    try:
        yield channel
    finally:
        try:
            channel.close()
            conn.close()
        except Exception:
            pass


@contextmanager
def rabbitmq_batch_channel(queue_name: str):
    """提供批次任務共用一個 connection/channel，用完才關閉"""
    conn = get_rabbitmq_connection()
    channel = conn.channel()
    channel.queue_declare(queue=queue_name, durable=True)
    try:
        yield channel
    finally:
        try:
            channel.close()
            conn.close()
        except Exception:
            pass


def send_rabbitmq_message(queue_name: str, payload: dict) -> None:
    """提供給 Flask Route 呼叫的快捷發送函式"""
    with rabbitmq_channel() as ch:
        ch.queue_declare(queue=queue_name, durable=True)
        ch.basic_publish(
            exchange="",
            routing_key=queue_name,
            body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            properties=pika.BasicProperties(
                delivery_mode=pika.DeliveryMode.Persistent
            ),
        )