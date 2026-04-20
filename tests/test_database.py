import pytest
from sqlalchemy import text
from repo.database import DatabaseManager, get_engine_config
from repo.config import Settings


class TestDatabase:
    """测试数据库功能"""
    
    def test_get_engine_config_sqlite(self):
        """测试SQLite引擎配置"""
        settings = Settings(DATABASE_URL="sqlite:///test.db", DEBUG=False)
        config = get_engine_config()
        assert config["connect_args"]["check_same_thread"] is False
        assert config["pool_size"] == 1
    
    def test_database_manager_init(self):
        """测试数据库管理器初始化"""
        manager = DatabaseManager()
        assert manager.engine is not None
        assert manager.SessionLocal is not None
    
    def test_database_manager_create_tables(self, engine):
        """测试创建表"""
        from repo.database import Base
        from repo.models import Fund, FundHolding
        
        manager = DatabaseManager()
        manager.create_tables()
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result]
            assert "funds" in tables
            assert "fund_holdings" in tables
    
    def test_database_manager_health_check(self):
        """测试数据库健康检查"""
        manager = DatabaseManager()
        assert manager.health_check() is True
    
    def test_session_scope_commit(self):
        """测试会话范围提交"""
        from repo.models import Fund
        
        manager = DatabaseManager()
        manager.create_tables()
        
        with manager.session_scope() as session:
            fund = Fund(
                fund_code="TEST001",
                fund_name="测试基金",
                fund_type="QDII"
            )
            session.add(fund)
        
        with manager.session_scope() as session:
            result = session.query(Fund).filter_by(fund_code="TEST001").first()
            assert result is not None
            assert result.fund_name == "测试基金"
    
    def test_session_scope_rollback(self):
        """测试会话范围回滚"""
        from repo.models import Fund
        from repo.exceptions import DatabaseException
        
        manager = DatabaseManager()
        manager.create_tables()
        
        with pytest.raises(DatabaseException):
            with manager.session_scope() as session:
                fund = Fund(
                    fund_code="TEST002",
                    fund_name="测试基金2",
                    fund_type="QDII"
                )
                session.add(fund)
                raise Exception("模拟错误")
        
        with manager.session_scope() as session:
            result = session.query(Fund).filter_by(fund_code="TEST002").first()
            assert result is None
