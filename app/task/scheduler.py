import sys
import traceback

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
import time
from util.common import common


logger = common.logger

#### 排程區塊 start ####
def add_task(scheduler):

### Schedule jobs to run Python scripts with ops configs ###
    logger.info('ops_audit_log start')
    # scheduler.add_job(
    #     func=audit_log.main,
    #     trigger='cron', hour='5,15',  minute=0, id='ops_audit_log'
    # )

    return scheduler
#### 排程區塊 end ####




def main():
    # Setup scheduler with a process pool
    executors = {
        # ops 機器 cpu 一般都不會很多
        # 使用虛擬 thread ThreadPoolExecutor , 取代實體 cpu mutil core 執行 ProcessPoolExecutor
        # 'default': ProcessPoolExecutor(max_workers=2)
        'default': ThreadPoolExecutor(max_workers=2)
    }
    job_defaults = {
        'coalesce': True,
        'misfire_grace_time': None
    }
    scheduler = BackgroundScheduler( job_defaults=job_defaults, executors=executors)
    scheduler = add_task(scheduler)

    scheduler.start()
    logger.info("Scheduler started. Press Ctrl+C to exit.")

    try:
        while True:
            time.sleep(10)
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
    main()