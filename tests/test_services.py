import pytest
from datetime import datetime, date
from unittest.mock import Mock, patch
from repo.services import FundService
from repo.models import Fund, FundHolding
from repo.exceptions import FundNotFoundException


class TestFundService:
    """测试基金服务"""
    
    @pytest.fixture
    def service(self, db_session):
        return FundService(db_session)
    
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
    
    def test_get_fund_list_empty(self, service):
        """测试获取基金列表-空"""
        total, funds = service.get_fund_list()
        assert total == 0
        assert funds == []
    
    def test_get_fund_list_with_data(self, service, sample_fund):
        """测试获取基金列表-有数据"""
        total, funds = service.get_fund_list()
        assert total == 1
        assert len(funds) == 1
        assert funds[0].fund_code == "000001"
    
    def test_get_fund_list_with_filter(self, service, sample_fund):
        """测试获取基金列表-带筛选"""
        total, funds = service.get_fund_list(fund_type="QDII")
        assert total == 1
        
        total, funds = service.get_fund_list(fund_type="股票型")
        assert total == 0
    
    def test_get_fund_list_pagination(self, service, db_session):
        """测试获取基金列表-分页"""
        for i in range(5):
            fund = Fund(
                fund_code=f"00000{i+1}",
                fund_name=f"测试基金{i+1}",
                fund_type="QDII"
            )
            db_session.add(fund)
        db_session.commit()
        
        total, funds = service.get_fund_list(skip=0, limit=3)
        assert total == 5
        assert len(funds) == 3
        
        total, funds = service.get_fund_list(skip=3, limit=3)
        assert len(funds) == 2
    
    def test_get_fund_by_code_exists(self, service, sample_fund):
        """测试通过代码获取基金-存在"""
        result = service.get_fund_by_code("000001")
        assert result is not None
        assert result.fund_code == "000001"
        assert result.fund_name == "测试基金"
    
    def test_get_fund_by_code_not_exists(self, service):
        """测试通过代码获取基金-不存在"""
        result = service.get_fund_by_code("999999")
        assert result is None
    
    def test_get_fund_holdings_empty(self, service, sample_fund):
        """测试获取基金持仓-空"""
        holdings = service.get_fund_holdings("000001")
        assert holdings == []
    
    def test_get_fund_holdings_with_data(self, service, db_session, sample_fund):
        """测试获取基金持仓-有数据"""
        holding1 = FundHolding(
            fund_code="000001",
            stock_code="00700",
            stock_name="腾讯",
            holding_ratio=10.5,
            holding_shares=1000.0,
            holding_value=500000.0,
            report_date=date(2024, 3, 31)
        )
        holding2 = FundHolding(
            fund_code="000001",
            stock_code="09988",
            stock_name="阿里",
            holding_ratio=8.5,
            holding_shares=2000.0,
            holding_value=400000.0,
            report_date=date(2024, 3, 31)
        )
        db_session.add(holding1)
        db_session.add(holding2)
        db_session.commit()
        
        holdings = service.get_fund_holdings("000001")
        assert len(holdings) == 2
        assert holdings[0].holding_ratio == 10.5
        assert holdings[1].holding_ratio == 8.5
    
    @patch.object(FundService, 'fetcher')
    def test_update_fund_data(self, mock_fetcher, service, db_session):
        """测试更新基金数据"""
        mock_fetcher.fetch_overseas_fund_list.return_value = [
            {
                'fund_code': '000001',
                'fund_name': '新基金',
                'fund_type': 'QDII',
                'fund_manager': '新经理',
                'fund_company': '新公司',
            }
        ]
        
        result = service.update_fund_data()
        
        assert result['total'] == 1
        assert result['new'] == 1
        assert result['updated'] == 0
        
        fund = db_session.query(Fund).filter_by(fund_code="000001").first()
        assert fund is not None
        assert fund.fund_name == "新基金"
    
    @patch.object(FundService, 'fetcher')
    def test_update_fund_data_existing(self, mock_fetcher, service, sample_fund, db_session):
        """测试更新基金数据-已存在"""
        mock_fetcher.fetch_overseas_fund_list.return_value = [
            {
                'fund_code': '000001',
                'fund_name': '更新后的基金',
                'fund_type': 'QDII-ETF',
            }
        ]
        
        result = service.update_fund_data()
        
        assert result['total'] == 1
        assert result['new'] == 0
        assert result['updated'] == 1
        
        fund = db_session.query(Fund).filter_by(fund_code="000001").first()
        assert fund.fund_name == "更新后的基金"
        assert fund.fund_type == "QDII-ETF"
    
    @patch.object(FundService, 'fetcher')
    def test_update_fund_nav(self, mock_fetcher, service, sample_fund, db_session):
        """测试更新基金净值"""
        mock_fetcher.update_all_fund_nav.return_value = {
            '000001': {
                'fund_code': '000001',
                'unit_nav': 1.8,
                'accumulated_nav': 2.5,
                'nav_date': date(2024, 1, 16)
            }
        }
        
        result = service.update_fund_nav()
        
        assert result['total'] == 1
        assert result['updated'] == 1
        
        fund = db_session.query(Fund).filter_by(fund_code="000001").first()
        assert fund.unit_nav == 1.8
        assert fund.accumulated_nav == 2.5
    
    @patch.object(FundService, 'fetcher')
    def test_update_fund_holdings(self, mock_fetcher, service, sample_fund, db_session):
        """测试更新基金持仓"""
        mock_fetcher.fetch_fund_holdings.return_value = [
            {
                'fund_code': '000001',
                'stock_code': '00700',
                'stock_name': '腾讯',
                'holding_ratio': 12.0,
                'holding_shares': 1500.0,
                'holding_value': 600000.0,
                'report_date': date(2024, 3, 31)
            }
        ]
        
        result = service.update_fund_holdings("000001")
        
        assert result['funds_updated'] == 1
        assert result['holdings_count'] == 1
        
        holdings = db_session.query(FundHolding).filter_by(fund_code="000001").all()
        assert len(holdings) == 1
        assert holdings[0].stock_name == "腾讯"
        assert holdings[0].holding_ratio == 12.0
    
    @patch.object(FundService, 'fetcher')
    def test_update_fund_holdings_all_funds(self, mock_fetcher, service, db_session):
        """测试更新所有基金持仓"""
        for i in range(3):
            fund = Fund(
                fund_code=f"00000{i+1}",
                fund_name=f"测试基金{i+1}",
                fund_type="QDII"
            )
            db_session.add(fund)
        db_session.commit()
        
        mock_fetcher.fetch_fund_holdings.return_value = [
            {
                'fund_code': '000001',
                'stock_code': '00700',
                'stock_name': '腾讯',
                'holding_ratio': 10.0,
            }
        ]
        
        result = service.update_fund_holdings()
        
        assert result['funds_updated'] == 3
        assert result['holdings_count'] == 3
    
    @patch.object(FundService, 'fetcher')
    def test_update_all_data(self, mock_fetcher, service):
        """测试全量更新数据"""
        mock_fetcher.fetch_overseas_fund_list.return_value = []
        mock_fetcher.update_all_fund_nav.return_value = {}
        mock_fetcher.fetch_fund_holdings.return_value = []
        
        result = service.update_all_data()
        
        assert 'funds' in result
        assert 'nav' in result
        assert 'holdings' in result
