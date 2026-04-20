import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from repo.database import Base
from repo.main import app
from repo.database import get_db
from repo.models import Fund, FundHolding


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_fund(db_session):
    fund = Fund(
        fund_code="000001",
        fund_name="测试基金",
        fund_type="QDII",
        fund_manager="张三",
        fund_company="测试基金公司",
        unit_nav=1.5,
        accumulated_nav=2.0
    )
    db_session.add(fund)
    db_session.commit()
    db_session.refresh(fund)
    return fund


@pytest.fixture
def sample_holding(db_session, sample_fund):
    holding = FundHolding(
        fund_code=sample_fund.fund_code,
        stock_code="600001",
        stock_name="测试股票",
        holding_ratio=5.5,
        holding_shares=10000,
        holding_value=50000
    )
    db_session.add(holding)
    db_session.commit()
    db_session.refresh(holding)
    return holding
