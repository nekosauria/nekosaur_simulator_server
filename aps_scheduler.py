import sys
import traceback

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
import time

from task import fetch_thecatapi_image
from util.common import common

logger = common.logger
config = common.config

def add_task(scheduler):
### Schedule jobs to run Python scripts configs ###
    logger.info('task thecatapi start')
    scheduler.add_job(
        func=fetch_thecatapi_image.trigger,
        kwargs={"count":int(config.get('task','thecatapi_fetch_count'))},
        trigger='cron',
        hour= config.get('task','thecatapi_cron_hour'),
        minute=int(config.get('task','thecatapi_cron_minute')),
        second=int(config.get('task','thecatapi_cron_second')),
        id=config.get('task','thecatapi_cron_id'),
    )

    return scheduler


def start_listening():
    # Setup scheduler with a thread pool
    executors = {
        # 機器 cpu 一般都不會很多
        # 使用虛擬 thread ThreadPoolExecutor , 取代實體 cpu mutil core 執行 ProcessPoolExecutor
        # 'default': ProcessPoolExecutor(max_workers=2)
        'default': ThreadPoolExecutor(max_workers=int(config.get('task','thread_pool_count')))
    }
    job_defaults = {
        'coalesce': True,
        'misfire_grace_time': None
    }
    scheduler = BackgroundScheduler( job_defaults=job_defaults, executors=executors)

    # 註冊定時任務
    scheduler = add_task(scheduler)
    scheduler.start()

    logger.info("Scheduler started. Press Ctrl+C to exit.")

    # keep alive
    try:
        while True:
            time.sleep(int(config.get('task','sleep_time')))
    except (KeyboardInterrupt, SystemExit) as k:
        scheduler.shutdown()
        logger.error("Scheduler shut down.")
        logger.error(f"Exception occurred: {k}", exc_info=True)
    except Exception as e:
        logger.error("Scheduler broken.")
        logger.error(f"Exception occurred: {e}", exc_info=True)
    finally:
        exc_type, exc_value, exc_traceback = traceback.format_exc(), *sys.exc_info()
        if exc_value:
            logger.error("Final error message:")
            logger.error(exc_value)


if __name__ == "__main__":
    start_listening()