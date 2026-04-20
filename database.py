from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
import logging
from typing import Generator

from repo.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        if settings.DATABASE_URL.startswith("sqlite"):
            _engine = create_engine(
                settings.DATABASE_URL,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=settings.DEBUG
            )
        else:
            _engine = create_engine(
                settings.DATABASE_URL,
                pool_pre_ping=True,
                pool_size=settings.DATABASE_POOL_SIZE,
                max_overflow=settings.DATABASE_MAX_OVERFLOW,
                pool_recycle=settings.DATABASE_POOL_RECYCLE,
                echo=settings.DEBUG
            )
        
        @event.listens_for(_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            if settings.DATABASE_URL.startswith("sqlite"):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA cache_size=-64000")
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
        
        logger.info("数据库引擎创建完成")
    
    return _engine


def get_session_local():
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionLocal


engine = get_engine()
SessionLocal = get_session_local()

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("数据库表创建完成")


def drop_db():
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    logger.info("数据库表删除完成")
