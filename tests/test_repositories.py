import pytest
from datetime import date

from repo.repositories import FundRepository, FundHoldingRepository, RepositoryFactory
from repo.models import Fund, FundHolding


class TestBaseRepository:
    def test_fund_repository_create(self, db_session):
        repo = FundRepository(db_session)
        fund_data = {
            "fund_code": "000001",
            "fund_name": "测试基金",
            "fund_type": "QDII",
        }

        fund = repo.create(fund_data)

        assert fund.fund_code == "000001"
        assert fund.fund_name == "测试基金"

    def test_fund_repository_get_by_code(self, db_session):
        repo = FundRepository(db_session)
        repo.create({"fund_code": "000001", "fund_name": "测试基金"})

        fund = repo.get_by_code("000001")

        assert fund is not None
        assert fund.fund_code == "000001"

    def test_fund_repository_get_by_code_not_found(self, db_session):
        repo = FundRepository(db_session)
        fund = repo.get_by_code("999999")
        assert fund is None

    def test_fund_repository_update(self, db_session):
        repo = FundRepository(db_session)
        fund = repo.create({"fund_code": "000001", "fund_name": "旧名称"})

        updated = repo.update(fund, {"fund_name": "新名称"})

        assert updated.fund_name == "新名称"
        assert updated.updated_at is not None

    def test_fund_repository_list_funds(self, db_session):
        repo = FundRepository(db_session)
        for i in range(15):
            repo.create({
                "fund_code": f"{i:06d}",
                "fund_name": f"基金{i}",
                "fund_type": "QDII" if i % 2 == 0 else "股票型"
            })

        total, funds = repo.list_funds(limit=10)
        assert total == 15
        assert len(funds) == 10

        total, funds = repo.list_funds(fund_type="QDII")
        assert total == 8

    def test_fund_repository_create_or_update_create(self, db_session):
        repo = FundRepository(db_session)
        fund_data = {"fund_code": "000001", "fund_name": "新基金"}

        fund, is_new = repo.create_or_update(fund_data)

        assert is_new is True
        assert fund.fund_code == "000001"

    def test_fund_repository_create_or_update_update(self, db_session):
        repo = FundRepository(db_session)
        repo.create({"fund_code": "000001", "fund_name": "旧基金"})

        fund, is_new = repo.create_or_update(
            {"fund_code": "000001", "fund_name": "更新的基金"}
        )

        assert is_new is False
        assert fund.fund_name == "更新的基金"

    def test_fund_holding_repository_replace_holdings(self, db_session):
        fund_repo = FundRepository(db_session)
        fund_repo.create({"fund_code": "000001", "fund_name": "测试基金"})

        holding_repo = FundHoldingRepository(db_session)

        holdings_data = [
            {
                "fund_code": "000001",
                "stock_code": "AAPL",
                "stock_name": "苹果",
                "holding_ratio": 5.5,
            },
            {
                "fund_code": "000001",
                "stock_code": "MSFT",
                "stock_name": "微软",
                "holding_ratio": 4.5,
            }
        ]

        count = holding_repo.replace_holdings("000001", holdings_data)
        assert count == 2

        holdings = holding_repo.get_by_fund_code("000001")
        assert len(holdings) == 2

    def test_repository_factory(self, db_session):
        factory = RepositoryFactory(db_session)

        fund_repo1 = factory.fund
        fund_repo2 = factory.fund
        assert fund_repo1 is fund_repo2

        holding_repo1 = factory.fund_holding
        holding_repo2 = factory.fund_holding
        assert holding_repo1 is holding_repo2
