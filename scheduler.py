from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
from repo.config import get_settings
from repo.database import SessionLocal
from repo.services import FundService

settings = get_settings()
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
    if not settings.SCHEDULER_ENABLED:
        logger.info("调度器已禁用，跳过启动")
        return

    scheduler.add_job(
        update_fund_data_job,
        CronTrigger(
            hour=settings.SCHEDULER_CRON_HOUR,
            minute=settings.SCHEDULER_CRON_MINUTE
        ),
        id="update_fund_data",
        name=f"每天{settings.SCHEDULER_CRON_HOUR}点{settings.SCHEDULER_CRON_MINUTE}分更新基金数据",
        replace_existing=True
    )

    scheduler.start()
    logger.info(
        f"定时任务调度器已启动，将在每天{settings.SCHEDULER_CRON_HOUR}点"
        f"{settings.SCHEDULER_CRON_MINUTE}分更新基金数据"
    )


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("定时任务调度器已关闭")
