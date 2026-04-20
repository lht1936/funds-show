from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import uvicorn

from repo.config import get_settings
from repo.database import engine, Base
from repo.routers import router as fund_router
from repo.scheduler import start_scheduler, shutdown_scheduler
from repo.exceptions import FundShowException, create_error_response

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
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

@app.exception_handler(FundShowException)
async def fund_show_exception_handler(request: Request, exc: FundShowException):
    logger.error(f"异常发生: {exc.error_code} - {exc.message}", extra=exc.details)
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(exc)
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"未捕获的异常: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "UNEXPECTED_ERROR",
                "message": "服务器内部错误",
                "details": {}
            }
        }
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
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
