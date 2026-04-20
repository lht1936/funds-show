from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
import logging
from repo.database import SessionLocal
from repo.services import FundService
from repo.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

scheduler = BackgroundScheduler(timezone=settings.SCHEDULER_TIMEZONE)


def job_listener(event):
    """任务执行监听器"""
    if event.exception:
        logger.error(f"定时任务执行失败: {event.job_id}, 错误: {event.exception}")
    else:
        logger.info(f"定时任务执行成功: {event.job_id}")


scheduler.add_listener(job_listener, EVENT_JOB_ERROR | EVENT_JOB_EXECUTED)


def update_fund_data_job():
    """更新基金数据定时任务"""
    logger.info("定时任务开始执行: 更新基金数据")
    db = SessionLocal()
    try:
        service = FundService(db)
        result = service.update_all_data()
        logger.info(f"定时任务执行完成: {result}")
    except Exception as e:
        logger.error(f"定时任务执行失败: {e}")
        raise
    finally:
        db.close()


def start_scheduler():
    """启动定时任务调度器"""
    if not settings.SCHEDULER_ENABLED:
        logger.info("定时任务已禁用")
        return
    
    try:
        scheduler.add_job(
            update_fund_data_job,
            CronTrigger(
                hour=settings.SCHEDULER_UPDATE_HOUR,
                minute=settings.SCHEDULER_UPDATE_MINUTE
            ),
            id="update_fund_data",
            name="每天早上{}点{}分更新基金数据".format(
                settings.SCHEDULER_UPDATE_HOUR,
                settings.SCHEDULER_UPDATE_MINUTE
            ),
            replace_existing=True,
            max_instances=1,
            coalesce=True
        )
        
        scheduler.start()
        logger.info(
            f"定时任务调度器已启动，将在每天 "
            f"{settings.SCHEDULER_UPDATE_HOUR:02d}:{settings.SCHEDULER_UPDATE_MINUTE:02d} "
            f"更新基金数据"
        )
    except Exception as e:
        logger.error(f"启动定时任务调度器失败: {e}")
        raise


def shutdown_scheduler():
    """关闭定时任务调度器"""
    try:
        if scheduler.running:
            scheduler.shutdown(wait=False)
            logger.info("定时任务调度器已关闭")
    except Exception as e:
        logger.error(f"关闭定时任务调度器失败: {e}")


def get_scheduler_status():
    """获取调度器状态"""
    return {
        "running": scheduler.running,
        "enabled": settings.SCHEDULER_ENABLED,
        "scheduled_time": f"{settings.SCHEDULER_UPDATE_HOUR:02d}:{settings.SCHEDULER_UPDATE_MINUTE:02d}",
        "timezone": settings.SCHEDULER_TIMEZONE,
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": str(job.next_run_time) if job.next_run_time else None
            }
            for job in scheduler.get_jobs()
        ]
    }
