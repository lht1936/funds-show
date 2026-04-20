import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///./test_fund_show.db"
os.environ["DEBUG"] = "true"
os.environ["SCHEDULER_ENABLED"] = "false"

from repo.database import Base, get_db
from repo.main import app
from repo.config import get_settings, Settings


@pytest.fixture(scope="session")
def test_settings():
    """测试配置"""
    return Settings(
        DATABASE_URL="sqlite:///./test_fund_show.db",
        DEBUG=True,
        SCHEDULER_ENABLED=False,
        LOG_LEVEL="DEBUG"
    )


@pytest.fixture(scope="session")
def engine():
    """创建测试数据库引擎"""
    engine = create_engine(
        "sqlite:///./test_fund_show.db",
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(engine):
    """创建数据库会话"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """创建测试客户端"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def sample_fund_data():
    """示例基金数据"""
    return {
        "fund_code": "000001",
        "fund_name": "测试海外基金",
        "fund_type": "QDII",
        "fund_manager": "测试经理",
        "fund_company": "测试公司",
        "unit_nav": 1.5,
        "accumulated_nav": 2.0,
    }


@pytest.fixture(scope="function")
def sample_holding_data():
    """示例持仓数据"""
    return {
        "stock_code": "00700",
        "stock_name": "腾讯控股",
        "holding_ratio": 10.5,
        "holding_shares": 10000.0,
        "holding_value": 5000000.0,
    }
