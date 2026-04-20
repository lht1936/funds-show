from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn

from repo.config import get_settings
from repo.database import engine, Base
from repo.routers import router as fund_router
from repo.scheduler import start_scheduler, shutdown_scheduler

settings = get_settings()

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("应用启动中...")
    
    Base.metadata.create_all(bind=engine)
    logger.info("数据库表创建完成")
    
    start_scheduler()
    logger.info("定时任务调度器已启动")
    
    yield
    
    shutdown_scheduler()
    logger.info("应用关闭")


app = FastAPI(
    title="海外投资基金数据服务",
    description="基于akshare获取海外投资基金净值和持仓信息，提供RESTful API接口",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(fund_router)


@app.get("/", tags=["root"])
def root():
    return {
        "message": "海外投资基金数据服务",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "repo.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG
    )
