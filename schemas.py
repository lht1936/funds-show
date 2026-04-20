from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class FundHoldingResponse(BaseModel):
    id: int
    fund_code: str
    stock_code: Optional[str] = None
    stock_name: Optional[str] = None
    holding_ratio: Optional[float] = None
    holding_shares: Optional[float] = None
    holding_value: Optional[float] = None
    report_date: Optional[date] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class FundResponse(BaseModel):
    fund_code: str
    fund_name: str
    fund_type: Optional[str] = None
    fund_manager: Optional[str] = None
    fund_company: Optional[str] = None
    establish_date: Optional[date] = None
    unit_nav: Optional[float] = None
    accumulated_nav: Optional[float] = None
    nav_date: Optional[date] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class FundListResponse(BaseModel):
    total: int
    funds: List[FundResponse]


class FundDetailResponse(BaseModel):
    fund: FundResponse
    holdings: List[FundHoldingResponse]


class MessageResponse(BaseModel):
    message: str
    success: bool
