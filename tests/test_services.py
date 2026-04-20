import pytest
from repo.services import FundService
from repo.repositories import FundRepository, FundHoldingRepository
from repo.exceptions import FundNotFoundError
from repo.models import Fund, FundHolding


class TestFundRepository:
    
    def test_get_list_empty(self, db_session):
        repo = FundRepository(db_session)
        total, funds = repo.get_list()
        assert total == 0
        assert funds == []
    
    def test_create_fund(self, db_session):
        repo = FundRepository(db_session)
        fund_data = {
            "fund_code": "000001",
            "fund_name": "测试基金",
            "fund_type": "QDII"
        }
        fund = repo.create(fund_data)
        assert fund.fund_code == "000001"
        assert fund.fund_name == "测试基金"
    
    def test_get_by_code(self, db_session, sample_fund):
        repo = FundRepository(db_session)
        fund = repo.get_by_code("000001")
        assert fund is not None
        assert fund.fund_name == "测试基金"
        
        fund = repo.get_by_code("999999")
        assert fund is None
    
    def test_update_fund(self, db_session, sample_fund):
        repo = FundRepository(db_session)
        updated_fund = repo.update(sample_fund, {
            "fund_name": "更新后的基金名称",
            "unit_nav": 2.0
        })
        assert updated_fund.fund_name == "更新后的基金名称"
        assert updated_fund.unit_nav == 2.0
    
    def test_bulk_upsert(self, db_session):
        repo = FundRepository(db_session)
        funds_data = [
            {
                "fund_code": "000001",
                "fund_name": "基金1",
                "fund_type": "QDII"
            },
            {
                "fund_code": "000002",
                "fund_name": "基金2",
                "fund_type": "QDII"
            }
        ]
        new_count, updated_count = repo.bulk_upsert(funds_data)
        assert new_count == 2
        assert updated_count == 0
        
        funds_data[0]["fund_name"] = "更新后的基金1"
        new_count, updated_count = repo.bulk_upsert(funds_data)
        assert new_count == 0
        assert updated_count == 1
    
    def test_get_all_codes(self, db_session, sample_fund):
        repo = FundRepository(db_session)
        codes = repo.get_all_codes()
        assert len(codes) == 1
        assert "000001" in codes


class TestFundHoldingRepository:
    
    def test_get_by_fund_code(self, db_session, sample_fund, sample_holding):
        repo = FundHoldingRepository(db_session)
        holdings = repo.get_by_fund_code(sample_fund.fund_code)
        assert len(holdings) == 1
        assert holdings[0].stock_code == "600001"
    
    def test_delete_by_fund_code(self, db_session, sample_fund, sample_holding):
        repo = FundHoldingRepository(db_session)
        count = repo.delete_by_fund_code(sample_fund.fund_code)
        assert count == 1
        
        holdings = repo.get_by_fund_code(sample_fund.fund_code)
        assert len(holdings) == 0
    
    def test_bulk_create(self, db_session, sample_fund):
        repo = FundHoldingRepository(db_session)
        holdings_data = [
            {
                "fund_code": sample_fund.fund_code,
                "stock_code": "600001",
                "stock_name": "股票1",
                "holding_ratio": 5.0
            },
            {
                "fund_code": sample_fund.fund_code,
                "stock_code": "600002",
                "stock_name": "股票2",
                "holding_ratio": 3.0
            }
        ]
        count = repo.bulk_create(holdings_data)
        assert count == 2
        
        holdings = repo.get_by_fund_code(sample_fund.fund_code)
        assert len(holdings) == 2


class TestFundService:
    
    def test_get_fund_list(self, db_session, sample_fund):
        service = FundService(db_session)
        total, funds = service.get_fund_list()
        assert total == 1
        assert len(funds) == 1
    
    def test_get_fund_by_code(self, db_session, sample_fund):
        service = FundService(db_session)
        fund = service.get_fund_by_code("000001")
        assert fund is not None
        assert fund.fund_name == "测试基金"
    
    def test_get_fund_holdings(self, db_session, sample_fund, sample_holding):
        service = FundService(db_session)
        holdings = service.get_fund_holdings(sample_fund.fund_code)
        assert len(holdings) == 1
