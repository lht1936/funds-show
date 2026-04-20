from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
from repo.database import get_db_context
from repo.services import FundService
from repo.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

scheduler = BackgroundScheduler()


def update_fund_data_job():
    logger.info("定时任务开始执行: 更新基金数据")
    try:
        with get_db_context() as db:
            service = FundService(db)
            result = service.update_all_data()
            logger.info(f"定时任务执行完成: {result}")
    except Exception as e:
        logger.error(f"定时任务执行失败: {e}", exc_info=True)


def start_scheduler():
    if not settings.SCHEDULER_ENABLED:
        logger.info("定时任务调度器已禁用")
        return
    
    scheduler.add_job(
        update_fund_data_job,
        CronTrigger(
            hour=settings.SCHEDULER_HOUR,
            minute=settings.SCHEDULER_MINUTE
        ),
        id="update_fund_data",
        name=f"每天{settings.SCHEDULER_HOUR}:{settings.SCHEDULER_MINUTE:02d}更新基金数据",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info(f"定时任务调度器已启动，将在每天{settings.SCHEDULER_HOUR}:{settings.SCHEDULER_MINUTE:02d}更新基金数据")


def shutdown_scheduler():
    scheduler.shutdown()
    logger.info("定时任务调度器已关闭")
