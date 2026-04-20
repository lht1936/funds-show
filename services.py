from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging
from repo.models import Fund, FundHolding
from repo.data_fetcher import OverseasFundDataFetcher
from repo.repositories import FundRepository, FundHoldingRepository
from repo.exceptions import DataFetchError
from repo.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class FundService:
    
    def __init__(self, db: Session):
        self.db = db
        self.fetcher = OverseasFundDataFetcher()
        self.fund_repo = FundRepository(db)
        self.holding_repo = FundHoldingRepository(db)
    
    def get_fund_list(self, skip: int = 0, limit: int = None, fund_type: Optional[str] = None) -> tuple:
        if limit is None:
            limit = settings.FUND_LIST_DEFAULT_LIMIT
        return self.fund_repo.get_list(skip=skip, limit=limit, fund_type=fund_type)
    
    def get_fund_by_code(self, fund_code: str) -> Optional[Fund]:
        return self.fund_repo.get_by_code(fund_code)
    
    def get_fund_holdings(self, fund_code: str) -> List[FundHolding]:
        return self.holding_repo.get_by_fund_code(fund_code)
    
    def update_fund_data(self) -> dict:
        logger.info("开始更新基金数据...")
        
        try:
            funds_data = self.fetcher.fetch_overseas_fund_list()
        except Exception as e:
            logger.error(f"获取基金数据失败: {e}")
            raise DataFetchError(source="overseas_fund_list", message=f"获取基金数据失败: {str(e)}")
        
        new_count, updated_count = self.fund_repo.bulk_upsert(funds_data)
        
        logger.info(f"基金数据更新完成: 新增 {new_count} 条, 更新 {updated_count} 条")
        
        return {
            "total": len(funds_data),
            "new": new_count,
            "updated": updated_count
        }
    
    def update_fund_nav(self) -> dict:
        logger.info("开始更新基金净值...")
        
        fund_codes = self.fund_repo.get_all_codes()
        
        try:
            nav_data = self.fetcher.update_all_fund_nav(fund_codes)
        except Exception as e:
            logger.error(f"获取净值数据失败: {e}")
            raise DataFetchError(source="fund_nav", message=f"获取净值数据失败: {str(e)}")
        
        updated_count = 0
        for code, nav in nav_data.items():
            fund = self.fund_repo.get_by_code(code)
            if fund:
                self.fund_repo.update(fund, {
                    'unit_nav': nav.get('unit_nav'),
                    'accumulated_nav': nav.get('accumulated_nav'),
                    'nav_date': nav.get('nav_date')
                })
                updated_count += 1
        
        logger.info(f"基金净值更新完成: 更新 {updated_count} 条")
        
        return {
            "total": len(fund_codes),
            "updated": updated_count
        }
    
    def update_fund_holdings(self, fund_code: Optional[str] = None) -> dict:
        logger.info("开始更新基金持仓数据...")
        
        if fund_code:
            funds = [self.fund_repo.get_by_code(fund_code)]
            funds = [f for f in funds if f is not None]
        else:
            _, funds = self.fund_repo.get_list(limit=settings.HOLDINGS_UPDATE_LIMIT)
        
        total_holdings = 0
        updated_funds = 0
        
        for fund in funds:
            try:
                holdings_data = self.fetcher.fetch_fund_holdings(fund.fund_code)
            except Exception as e:
                logger.error(f"获取基金 {fund.fund_code} 持仓失败: {e}")
                continue
            
            if holdings_data:
                count = self.holding_repo.replace_holdings(fund.fund_code, holdings_data)
                total_holdings += count
                updated_funds += 1
        
        logger.info(f"基金持仓更新完成: 更新 {updated_funds} 只基金, 共 {total_holdings} 条持仓记录")
        
        return {
            "funds_updated": updated_funds,
            "holdings_count": total_holdings
        }
    
    def update_all_data(self) -> dict:
        logger.info("开始全量更新数据...")
        
        fund_result = self.update_fund_data()
        nav_result = self.update_fund_nav()
        holdings_result = self.update_fund_holdings()
        
        return {
            "funds": fund_result,
            "nav": nav_result,
            "holdings": holdings_result
        }
