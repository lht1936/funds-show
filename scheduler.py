from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
from database import SessionLocal
from services import FundService
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

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
    if not settings.SCHEDULER_ENABLED:
        logger.info("定时任务调度器已禁用")
        return
    
    scheduler.add_job(
        update_fund_data_job,
        CronTrigger(hour=settings.SCHEDULER_HOUR, minute=settings.SCHEDULER_MINUTE),
        id=settings.SCHEDULER_JOB_ID,
        name=settings.SCHEDULER_JOB_NAME,
        replace_existing=True
    )
    
    scheduler.start()
    logger.info(f"定时任务调度器已启动，将在每天 {settings.SCHEDULER_HOUR:02d}:{settings.SCHEDULER_MINUTE:02d} 更新基金数据")


def shutdown_scheduler():
    scheduler.shutdown()
    logger.info("定时任务调度器已关闭")
