import pytest
from datetime import datetime, date
from repo.models import Fund, FundHolding


class TestRouters:
    """测试路由"""
    
    @pytest.fixture
    def sample_fund(self, db_session):
        """创建示例基金"""
        fund = Fund(
            fund_code="000001",
            fund_name="测试基金",
            fund_type="QDII",
            fund_manager="测试经理",
            fund_company="测试公司",
            establish_date=date(2020, 1, 1),
            unit_nav=1.5,
            accumulated_nav=2.0,
            nav_date=date(2024, 1, 15),
            updated_at=datetime.utcnow()
        )
        db_session.add(fund)
        db_session.commit()
        return fund
    
    @pytest.fixture
    def sample_holdings(self, db_session, sample_fund):
        """创建示例持仓"""
        holdings = [
            FundHolding(
                fund_code="000001",
                stock_code="00700",
                stock_name="腾讯控股",
                holding_ratio=10.5,
                holding_shares=1000.0,
                holding_value=500000.0,
                report_date=date(2024, 3, 31)
            ),
            FundHolding(
                fund_code="000001",
                stock_code="09988",
                stock_name="阿里巴巴",
                holding_ratio=8.5,
                holding_shares=2000.0,
                holding_value=400000.0,
                report_date=date(2024, 3, 31)
            )
        ]
        for holding in holdings:
            db_session.add(holding)
        db_session.commit()
        return holdings
    
    def test_root_endpoint(self, client):
        """测试根端点"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "docs" in data
        assert "version" in data
    
    def test_health_check(self, client):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_get_fund_list_empty(self, client):
        """测试获取基金列表-空"""
        response = client.get("/api/v1/funds")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["funds"] == []
    
    def test_get_fund_list_with_data(self, client, sample_fund):
        """测试获取基金列表-有数据"""
        response = client.get("/api/v1/funds")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["funds"]) == 1
        assert data["funds"][0]["fund_code"] == "000001"
        assert data["funds"][0]["fund_name"] == "测试基金"
    
    def test_get_fund_list_pagination(self, client, db_session):
        """测试获取基金列表-分页"""
        for i in range(5):
            fund = Fund(
                fund_code=f"00000{i+1}",
                fund_name=f"测试基金{i+1}",
                fund_type="QDII"
            )
            db_session.add(fund)
        db_session.commit()
        
        response = client.get("/api/v1/funds?skip=0&limit=3")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["funds"]) == 3
        
        response = client.get("/api/v1/funds?skip=3&limit=3")
        data = response.json()
        assert len(data["funds"]) == 2
    
    def test_get_fund_list_filter(self, client, db_session):
        """测试获取基金列表-筛选"""
        fund1 = Fund(fund_code="000001", fund_name="基金A", fund_type="QDII")
        fund2 = Fund(fund_code="000002", fund_name="基金B", fund_type="股票型")
        db_session.add(fund1)
        db_session.add(fund2)
        db_session.commit()
        
        response = client.get("/api/v1/funds?fund_type=QDII")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["funds"][0]["fund_type"] == "QDII"
    
    def test_get_fund_detail_exists(self, client, sample_fund, sample_holdings):
        """测试获取基金详情-存在"""
        response = client.get("/api/v1/funds/000001")
        assert response.status_code == 200
        data = response.json()
        assert data["fund"]["fund_code"] == "000001"
        assert data["fund"]["fund_name"] == "测试基金"
        assert len(data["holdings"]) == 2
    
    def test_get_fund_detail_not_exists(self, client):
        """测试获取基金详情-不存在"""
        response = client.get("/api/v1/funds/999999")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error_code"] == "FUND_NOT_FOUND"
    
    def test_get_fund_holdings_exists(self, client, sample_fund, sample_holdings):
        """测试获取基金持仓-存在"""
        response = client.get("/api/v1/funds/000001/holdings")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["stock_name"] == "腾讯控股"
        assert data[1]["stock_name"] == "阿里巴巴"
    
    def test_get_fund_holdings_not_exists(self, client):
        """测试获取基金持仓-基金不存在"""
        response = client.get("/api/v1/funds/999999/holdings")
        assert response.status_code == 404
    
    @pytest.mark.skip(reason="需要mock外部API调用")
    def test_trigger_update_all(self, client):
        """测试触发全量更新"""
        response = client.post("/api/v1/funds/update?update_type=all")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @pytest.mark.skip(reason="需要mock外部API调用")
    def test_trigger_update_funds(self, client):
        """测试触发基金列表更新"""
        response = client.post("/api/v1/funds/update?update_type=funds")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @pytest.mark.skip(reason="需要mock外部API调用")
    def test_trigger_update_nav(self, client):
        """测试触发净值更新"""
        response = client.post("/api/v1/funds/update?update_type=nav")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @pytest.mark.skip(reason="需要mock外部API调用")
    def test_trigger_update_holdings(self, client):
        """测试触发持仓更新"""
        response = client.post("/api/v1/funds/update?update_type=holdings")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_trigger_update_invalid_type(self, client):
        """测试触发更新-无效类型"""
        response = client.post("/api/v1/funds/update?update_type=invalid")
        assert response.status_code == 400
