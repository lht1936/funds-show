from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import logging

from repo.models import Fund, FundHolding
from repo.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class BaseRepository(ABC):
    def __init__(self, db: Session):
        self.db = db
    
    def _handle_db_error(self, operation: str, error: Exception):
        logger.error(f"Database error during {operation}: {str(error)}", exc_info=True)
        self.db.rollback()
        raise DatabaseError(operation=operation, message=f"数据库操作失败: {str(error)}")


class FundRepository(BaseRepository):
    
    def get_list(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        fund_type: Optional[str] = None
    ) -> Tuple[int, List[Fund]]:
        try:
            query = self.db.query(Fund)
            
            if fund_type:
                query = query.filter(Fund.fund_type.ilike(f"%{fund_type}%"))
            
            total = query.count()
            funds = query.order_by(Fund.updated_at.desc()).offset(skip).limit(limit).all()
            
            return total, funds
        except Exception as e:
            self._handle_db_error("get_fund_list", e)
    
    def get_by_code(self, fund_code: str) -> Optional[Fund]:
        try:
            return self.db.query(Fund).filter(Fund.fund_code == fund_code).first()
        except Exception as e:
            self._handle_db_error("get_fund_by_code", e)
    
    def create(self, fund_data: dict) -> Fund:
        try:
            fund = Fund(**fund_data)
            self.db.add(fund)
            self.db.commit()
            self.db.refresh(fund)
            return fund
        except Exception as e:
            self._handle_db_error("create_fund", e)
    
    def update(self, fund: Fund, fund_data: dict) -> Fund:
        try:
            for key, value in fund_data.items():
                if value is not None:
                    setattr(fund, key, value)
            fund.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(fund)
            return fund
        except Exception as e:
            self._handle_db_error("update_fund", e)
    
    def bulk_upsert(self, funds_data: List[dict]) -> Tuple[int, int]:
        try:
            updated_count = 0
            new_count = 0
            
            for fund_data in funds_data:
                existing_fund = self.get_by_code(fund_data['fund_code'])
                
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
            return new_count, updated_count
        except Exception as e:
            self._handle_db_error("bulk_upsert_funds", e)
    
    def get_all_codes(self) -> List[str]:
        try:
            return [f.fund_code for f in self.db.query(Fund.fund_code).all()]
        except Exception as e:
            self._handle_db_error("get_all_fund_codes", e)


class FundHoldingRepository(BaseRepository):
    
    def get_by_fund_code(self, fund_code: str) -> List[FundHolding]:
        try:
            return self.db.query(FundHolding).filter(
                FundHolding.fund_code == fund_code
            ).order_by(FundHolding.holding_ratio.desc().nullslast()).all()
        except Exception as e:
            self._handle_db_error("get_fund_holdings", e)
    
    def delete_by_fund_code(self, fund_code: str) -> int:
        try:
            count = self.db.query(FundHolding).filter(
                FundHolding.fund_code == fund_code
            ).delete()
            self.db.commit()
            return count
        except Exception as e:
            self._handle_db_error("delete_fund_holdings", e)
    
    def bulk_create(self, holdings_data: List[dict]) -> int:
        try:
            holdings = [FundHolding(**data) for data in holdings_data]
            self.db.add_all(holdings)
            self.db.commit()
            return len(holdings)
        except Exception as e:
            self._handle_db_error("bulk_create_holdings", e)
    
    def replace_holdings(self, fund_code: str, holdings_data: List[dict]) -> int:
        try:
            self.delete_by_fund_code(fund_code)
            return self.bulk_create(holdings_data)
        except Exception as e:
            self._handle_db_error("replace_holdings", e)
