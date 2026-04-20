from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator, Optional
import logging
import time
from repo.config import get_settings
from repo.exceptions import DatabaseException

logger = logging.getLogger(__name__)
settings = get_settings()


def get_engine_config():
    """获取数据库引擎配置"""
    base_config = {
        "echo": settings.DEBUG,
        "pool_pre_ping": True,
    }
    
    if settings.DATABASE_URL.startswith("sqlite"):
        return {
            **base_config,
            "connect_args": {"check_same_thread": False},
            "pool_size": 1,
            "max_overflow": 0,
        }
    else:
        return {
            **base_config,
            "pool_size": settings.DB_POOL_SIZE,
            "max_overflow": settings.DB_MAX_OVERFLOW,
            "pool_recycle": settings.DB_POOL_RECYCLE,
            "pool_timeout": settings.DB_POOL_TIMEOUT,
        }


engine = create_engine(settings.DATABASE_URL, **get_engine_config())


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """SQLite 连接初始化设置"""
    if settings.DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()


@event.listens_for(engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """记录SQL执行开始时间"""
    conn.info.setdefault('query_start_time', []).append(time.time())


@event.listens_for(engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """记录SQL执行时间"""
    start_time = conn.info['query_start_time'].pop(-1)
    total_time = time.time() - start_time
    if total_time > settings.SLOW_QUERY_THRESHOLD:
        logger.warning(f"慢查询 ({total_time:.2f}s): {statement[:100]}...")


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def get_session(self) -> Generator[Session, None, None]:
        """获取数据库会话（生成器方式）"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """提供事务范围的会话上下文管理器"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库事务回滚: {e}")
            raise DatabaseException(
                message=f"数据库操作失败: {str(e)}",
                operation="transaction"
            )
        finally:
            session.close()
    
    def create_tables(self):
        """创建所有表"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("数据库表创建完成")
        except Exception as e:
            logger.error(f"创建数据库表失败: {e}")
            raise DatabaseException(
                message=f"创建数据库表失败: {str(e)}",
                operation="create_tables"
            )
    
    def drop_tables(self):
        """删除所有表"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("数据库表删除完成")
        except Exception as e:
            logger.error(f"删除数据库表失败: {e}")
            raise DatabaseException(
                message=f"删除数据库表失败: {str(e)}",
                operation="drop_tables"
            )
    
    def health_check(self) -> bool:
        """数据库健康检查"""
        try:
            with self.session_scope() as session:
                session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"数据库健康检查失败: {e}")
            return False


def get_db() -> Generator[Session, None, None]:
    """FastAPI依赖注入用的数据库会话获取函数"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"数据库会话错误: {e}")
        raise
    finally:
        db.close()


def get_db_manager() -> DatabaseManager:
    """获取数据库管理器实例"""
    return DatabaseManager()
