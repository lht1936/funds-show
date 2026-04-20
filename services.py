from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from repo.config import get_settings
from repo.repositories import RepositoryFactory
from repo.data_fetcher import OverseasFundDataFetcher
from repo.exceptions import FundNotFoundError, InvalidParameterError
from repo.models import Fund, FundHolding

settings = get_settings()

logger = logging.getLogger(__name__)


class FundService:
    def __init__(self, db: Session):
        self.db = db
        self.repos = RepositoryFactory(db)
        self.fetcher = OverseasFundDataFetcher()

    def get_fund_list(
        self,
        skip: int = 0,
        limit: int = settings.DEFAULT_LIST_LIMIT,
        fund_type: Optional[str] = None
    ) -> tuple[int, List[Fund]]:
        if skip < 0:
            raise InvalidParameterError(
                param_name="skip",
                reason="必须大于等于0"
            )
        if limit < 1 or limit > settings.MAX_SERVICE_LIMIT:
            raise InvalidParameterError(
                param_name="limit",
                reason=f"必须在1到{settings.MAX_SERVICE_LIMIT}之间"
            )

        return self.repos.fund.list_funds(skip, limit, fund_type)

    def get_fund_by_code(self, fund_code: str) -> Fund:
        if not fund_code:
            raise InvalidParameterError(
                param_name="fund_code",
                reason="基金代码不能为空"
            )

        fund = self.repos.fund.get_by_code(fund_code)
        if not fund:
            raise FundNotFoundError(fund_code=fund_code)
        return fund

    def get_fund_holdings(self, fund_code: str) -> List[FundHolding]:
        self.get_fund_by_code(fund_code)
        return self.repos.fund_holding.get_by_fund_code(fund_code)

    def update_fund_data(self) -> Dict[str, int]:
        logger.info("开始更新基金数据...")

        funds_data = self.fetcher.fetch_overseas_fund_list()

        new_count = 0
        updated_count = 0

        for fund_data in funds_data:
            fund_code = fund_data.get('fund_code')
            if not fund_code:
                continue

            _, is_new = self.repos.fund.create_or_update(fund_data)
            if is_new:
                new_count += 1
            else:
                updated_count += 1

        logger.info(f"基金数据更新完成: 新增 {new_count} 条, 更新 {updated_count} 条")

        return {
            "total": len(funds_data),
            "new": new_count,
            "updated": updated_count
        }

    def update_fund_nav(self) -> Dict[str, int]:
        logger.info("开始更新基金净值...")

        fund_codes = self.repos.fund.get_all_codes()
        nav_data = self.fetcher.update_all_fund_nav(fund_codes)

        updated_count = 0
        for code, nav in nav_data.items():
            try:
                fund = self.repos.fund.get_by_code(code)
                if fund:
                    update_data = {
                        'unit_nav': nav.get('unit_nav'),
                        'accumulated_nav': nav.get('accumulated_nav'),
                        'nav_date': nav.get('nav_date'),
                    }
                    self.repos.fund.update(fund, update_data)
                    updated_count += 1
            except Exception as e:
                logger.error(f"更新基金 {code} 净值失败: {e}")

        logger.info(f"基金净值更新完成: 更新 {updated_count} 条")

        return {
            "total": len(fund_codes),
            "updated": updated_count
        }

    def update_fund_holdings(
        self,
        fund_code: Optional[str] = None,
        max_funds: int = settings.HOLDINGS_UPDATE_MAX_FUNDS
    ) -> Dict[str, int]:
        logger.info("开始更新基金持仓数据...")

        if fund_code:
            fund = self.get_fund_by_code(fund_code)
            funds = [fund]
        else:
            _, funds = self.repos.fund.list_funds(limit=max_funds)

        total_holdings = 0
        updated_funds = 0

        for fund in funds:
            try:
                holdings_data = self.fetcher.fetch_fund_holdings(fund.fund_code)
                if holdings_data:
                    count = self.repos.fund_holding.replace_holdings(
                        fund.fund_code,
                        holdings_data
                    )
                    total_holdings += count
                    updated_funds += 1
            except Exception as e:
                logger.error(f"更新基金 {fund.fund_code} 持仓失败: {e}")

        logger.info(f"基金持仓更新完成: 更新 {updated_funds} 只基金, 共 {total_holdings} 条持仓记录")

        return {
            "funds_updated": updated_funds,
            "holdings_count": total_holdings
        }

    def update_all_data(self) -> Dict[str, Any]:
        logger.info("开始全量更新数据...")

        fund_result = self.update_fund_data()
        nav_result = self.update_fund_nav()
        holdings_result = self.update_fund_holdings()

        return {
            "funds": fund_result,
            "nav": nav_result,
            "holdings": holdings_result
        }
