from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging
from models import Fund, FundHolding
from data_fetcher import OverseasFundDataFetcher

logger = logging.getLogger(__name__)


class FundService:
    
    def __init__(self, db: Session):
        self.db = db
        self.fetcher = OverseasFundDataFetcher()
    
    def get_fund_list(self, skip: int = 0, limit: int = 100, fund_type: Optional[str] = None) -> tuple:
        query = self.db.query(Fund)
        
        if fund_type:
            query = query.filter(Fund.fund_type.ilike(f"%{fund_type}%"))
        
        total = query.count()
        funds = query.order_by(Fund.updated_at.desc()).offset(skip).limit(limit).all()
        
        return total, funds
    
    def get_fund_by_code(self, fund_code: str) -> Optional[Fund]:
        return self.db.query(Fund).filter(Fund.fund_code == fund_code).first()
    
    def get_fund_holdings(self, fund_code: str) -> List[FundHolding]:
        return self.db.query(FundHolding).filter(
            FundHolding.fund_code == fund_code
        ).order_by(FundHolding.holding_ratio.desc().nullslast()).all()
    
    def update_fund_data(self) -> dict:
        logger.info("开始更新基金数据...")
        
        funds_data = self.fetcher.fetch_overseas_fund_list()
        
        updated_count = 0
        new_count = 0
        
        for fund_data in funds_data:
            existing_fund = self.get_fund_by_code(fund_data['fund_code'])
            
            if existing_fund:
                for key, value in fund_data.items():
                    if value is not None:
                        setattr(existing_fund, key, value)
                existing_fund.updated_at = datetime.utcnow()
                updated_count += 1
            else:
                new_fund = Fund(**fund_data)
                self.db.add(new_fund)
                new_count += 1
        
        self.db.commit()
        logger.info(f"基金数据更新完成: 新增 {new_count} 条, 更新 {updated_count} 条")
        
        return {
            "total": len(funds_data),
            "new": new_count,
            "updated": updated_count
        }
    
    def update_fund_nav(self) -> dict:
        logger.info("开始更新基金净值...")
        
        funds = self.db.query(Fund).all()
        fund_codes = [f.fund_code for f in funds]
        
        nav_data = self.fetcher.update_all_fund_nav(fund_codes)
        
        updated_count = 0
        for code, nav in nav_data.items():
            fund = self.get_fund_by_code(code)
            if fund:
                fund.unit_nav = nav.get('unit_nav')
                fund.accumulated_nav = nav.get('accumulated_nav')
                fund.nav_date = nav.get('nav_date')
                fund.updated_at = datetime.utcnow()
                updated_count += 1
        
        self.db.commit()
        logger.info(f"基金净值更新完成: 更新 {updated_count} 条")
        
        return {
            "total": len(fund_codes),
            "updated": updated_count
        }
    
    def update_fund_holdings(self, fund_code: Optional[str] = None) -> dict:
        logger.info("开始更新基金持仓数据...")
        
        if fund_code:
            funds = [self.get_fund_by_code(fund_code)]
            funds = [f for f in funds if f is not None]
        else:
            funds = self.db.query(Fund).limit(50).all()
        
        total_holdings = 0
        updated_funds = 0
        
        for fund in funds:
            holdings_data = self.fetcher.fetch_fund_holdings(fund.fund_code)
            
            if holdings_data:
                self.db.query(FundHolding).filter(
                    FundHolding.fund_code == fund.fund_code
                ).delete()
                
                for holding_data in holdings_data:
                    holding = FundHolding(**holding_data)
                    self.db.add(holding)
                    total_holdings += 1
                
                updated_funds += 1
        
        self.db.commit()
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
