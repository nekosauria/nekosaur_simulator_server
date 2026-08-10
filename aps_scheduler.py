from dataclasses import dataclass, field
from typing import Callable
import time

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_MISSED, EVENT_JOB_EXECUTED

from task import fetch_thecatapi
from task import image_daemon_process
from util.common import common

logger = common.logger
config = common.config


# 命名慣例說明:
# 「task」= 我們自己的抽象 (TaskDefinition)，代表一個要被排程的工作定義
# 「job」 = apscheduler 官方用語 (add_job / event.job_id / job_listener)，
#          代表 task 被註冊進 scheduler 後、由 apscheduler 管理的執行單位
# 兩者概念上是一對一，但故意不混用同一個字，避免跟 apscheduler 內建 API 撞名


@dataclass
class TaskDefinition:
    name: str                          # task 識別名稱，同時是 config section 裡的 key prefix
    func: Callable[..., None]           # 要執行的 function
    kwargs: dict = field(default_factory=dict)  # func 執行時要用的完整參數，由呼叫端自己組好


def register_task(scheduler: BackgroundScheduler, task: TaskDefinition) -> None:
    """
    只負責把 TaskDefinition 轉成 apscheduler 的 job，不碰參數怎麼來的。
    cron 時間欄位維持命名慣例，因為這是「怎麼排程」的共通邏輯，跟 func 需要什麼參數是兩回事。
    """
    logger.info(f"task {task.name} start")
    scheduler.add_job(
        func=task.func,
        kwargs=task.kwargs,
        trigger='cron',
        hour=config.get('task', f'{task.name}_cron_hour'),
        minute=int(config.get('task', f'{task.name}_cron_minute')),
        second=int(config.get('task', f'{task.name}_cron_second')),
        id=config.get('task', f'{task.name}_cron_id'),
    )


# 註冊需要的定時任務
def build_fetch_thecatapi_task() -> TaskDefinition:
    """
    fetch_thecatapi task 需要什麼參數，由這裡自己決定、自己去 config 讀。
    register_task 完全不用知道 fetch_thecatapi 需要 count。
    """
    return TaskDefinition(
        name="fetch_thecatapi",
        func=fetch_thecatapi.trigger,
        kwargs={},
    )

def build_image_daemon_process_task() -> TaskDefinition:
    return TaskDefinition(
        name="image_daemon_process",
        func=image_daemon_process.trigger,
        kwargs={},
    )

TASKS: list[TaskDefinition] = [
    build_fetch_thecatapi_task(),
    build_image_daemon_process_task(),
]


def add_task(scheduler: BackgroundScheduler) -> BackgroundScheduler:
    for task in TASKS:
        register_task(scheduler, task)
    return scheduler


# === job(apscheduler) 層級全域例外處理 (Global Job Error Handlers) ===
def job_listener(event):
    if event.exception:
        logger.error(f"Job [{event.job_id}] raised an exception")
        logger.error(f"Exception: {event.exception}")
        logger.error(f"Traceback:\n{event.traceback}")
    elif event.code == EVENT_JOB_MISSED:
        logger.warning(f"Job [{event.job_id}] missed its scheduled run time")
    else:
        logger.info(f"Job [{event.job_id}] executed successfully")


# === aps daemon init ===
def start_listening():
    executors = {
        'default': ThreadPoolExecutor(max_workers=int(config.get('task', 'thread_pool_count')))
    }
    job_defaults = {
        'coalesce': True,
        'misfire_grace_time': None
    }
    scheduler = BackgroundScheduler(job_defaults=job_defaults, executors=executors)

    scheduler = add_task(scheduler)
    scheduler.add_listener(job_listener, EVENT_JOB_ERROR | EVENT_JOB_MISSED | EVENT_JOB_EXECUTED)
    scheduler.start()

    logger.info("Scheduler started. Press Ctrl+C to exit.")

    # aps daemon 意外處理
    try:
        while True:
            time.sleep(int(config.get('task', 'sleep_time')))
    except (KeyboardInterrupt, SystemExit) as k:
        logger.info("Received shutdown signal.")
        logger.info(f"Signal: {k}")
    except Exception as e:
        logger.error("Scheduler broken.")
        logger.error(f"Exception occurred: {e}", exc_info=True)
    finally:
        scheduler.shutdown()
        logger.info("Scheduler shut down.")


if __name__ == "__main__":
    start_listening()