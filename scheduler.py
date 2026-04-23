from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
from database import SessionLocal
from services import FundService

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def update_fund_data_job():
    logger.info("定时任务开始执行: 更新基金数据")
    db = SessionLocal()
    try:
        service = FundService(db)
        result = service.update_all_data()
        logger.info(f"定时任务执行完成: {result}")
    except Exception as e:
        logger.error(f"定时任务执行失败: {e}")
    finally:
        db.close()


def start_scheduler():
    scheduler.add_job(
        update_fund_data_job,
        CronTrigger(hour=4, minute=0),
        id="update_fund_data",
        name="每天早上4点更新基金数据",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("定时任务调度器已启动，将在每天早上4点更新基金数据")


def shutdown_scheduler():
    scheduler.shutdown()
    logger.info("定时任务调度器已关闭")
