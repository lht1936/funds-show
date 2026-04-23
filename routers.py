from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from services import FundService
from config import get_settings
from schemas import (
    FundResponse, 
    FundListResponse, 
    FundDetailResponse, 
    FundHoldingResponse,
    MessageResponse
)

settings = get_settings()
router = APIRouter(prefix=settings.API_PREFIX, tags=["funds"])


@router.get("", response_model=FundListResponse, summary="获取基金列表")
def get_fund_list(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回的记录数"),
    fund_type: Optional[str] = Query(None, description="基金类型筛选"),
    db: Session = Depends(get_db)
):
    service = FundService(db)
    total, funds = service.get_fund_list(skip=skip, limit=limit, fund_type=fund_type)
    
    return FundListResponse(
        total=total,
        funds=[FundResponse.model_validate(fund) for fund in funds]
    )


@router.get("/{fund_code}", response_model=FundDetailResponse, summary="获取基金详情及持仓信息")
def get_fund_detail(
    fund_code: str,
    db: Session = Depends(get_db)
):
    service = FundService(db)
    fund = service.get_fund_by_code(fund_code)
    
    if not fund:
        raise HTTPException(status_code=404, detail=f"基金 {fund_code} 不存在")
    
    holdings = service.get_fund_holdings(fund_code)
    
    return FundDetailResponse(
        fund=FundResponse.model_validate(fund),
        holdings=[FundHoldingResponse.model_validate(h) for h in holdings]
    )


@router.get("/{fund_code}/holdings", response_model=list[FundHoldingResponse], summary="获取基金持仓信息")
def get_fund_holdings(
    fund_code: str,
    db: Session = Depends(get_db)
):
    service = FundService(db)
    fund = service.get_fund_by_code(fund_code)
    
    if not fund:
        raise HTTPException(status_code=404, detail=f"基金 {fund_code} 不存在")
    
    holdings = service.get_fund_holdings(fund_code)
    
    return [FundHoldingResponse.model_validate(h) for h in holdings]


@router.post("/update", response_model=MessageResponse, summary="手动触发数据更新")
def trigger_update(
    update_type: str = Query("all", description="更新类型: all, funds, nav, holdings"),
    db: Session = Depends(get_db)
):
    service = FundService(db)
    
    try:
        if update_type == "all":
            result = service.update_all_data()
            return MessageResponse(
                message=f"全量更新完成: {result}",
                success=True
            )
        elif update_type == "funds":
            result = service.update_fund_data()
            return MessageResponse(
                message=f"基金列表更新完成: {result}",
                success=True
            )
        elif update_type == "nav":
            result = service.update_fund_nav()
            return MessageResponse(
                message=f"净值更新完成: {result}",
                success=True
            )
        elif update_type == "holdings":
            result = service.update_fund_holdings()
            return MessageResponse(
                message=f"持仓更新完成: {result}",
                success=True
            )
        else:
            raise HTTPException(status_code=400, detail="无效的更新类型")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")
