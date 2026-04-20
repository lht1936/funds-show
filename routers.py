from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from repo.database import get_db
from repo.services import FundService
from repo.schemas import (
    FundResponse, 
    FundListResponse, 
    FundDetailResponse, 
    FundHoldingResponse,
    MessageResponse
)
from repo.exceptions import FundShowException, FundNotFoundException, raise_http_exception
from repo.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix=settings.API_PREFIX + "/funds", tags=["funds"])


@router.get("", response_model=FundListResponse, summary="获取基金列表")
def get_fund_list(
    skip: int = Query(settings.DEFAULT_SKIP, ge=0, description="跳过的记录数"),
    limit: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="返回的记录数"),
    fund_type: Optional[str] = Query(None, description="基金类型筛选"),
    db: Session = Depends(get_db)
):
    """
    获取基金列表，支持分页和类型筛选
    """
    try:
        service = FundService(db)
        total, funds = service.get_fund_list(skip=skip, limit=limit, fund_type=fund_type)
        
        return FundListResponse(
            total=total,
            funds=[FundResponse.model_validate(fund) for fund in funds]
        )
    except FundShowException as e:
        raise_http_exception(e)


@router.get("/{fund_code}", response_model=FundDetailResponse, summary="获取基金详情及持仓信息")
def get_fund_detail(
    fund_code: str,
    db: Session = Depends(get_db)
):
    """
    获取指定基金的详细信息及持仓数据
    """
    try:
        service = FundService(db)
        fund = service.get_fund_or_raise(fund_code)
        holdings = service.get_fund_holdings(fund_code)
        
        return FundDetailResponse(
            fund=FundResponse.model_validate(fund),
            holdings=[FundHoldingResponse.model_validate(h) for h in holdings]
        )
    except FundShowException as e:
        raise_http_exception(e)


@router.get("/{fund_code}/holdings", response_model=list[FundHoldingResponse], summary="获取基金持仓信息")
def get_fund_holdings(
    fund_code: str,
    db: Session = Depends(get_db)
):
    """
    获取指定基金的持仓明细
    """
    try:
        service = FundService(db)
        service.get_fund_or_raise(fund_code)
        holdings = service.get_fund_holdings(fund_code)
        
        return [FundHoldingResponse.model_validate(h) for h in holdings]
    except FundShowException as e:
        raise_http_exception(e)


@router.post("/update", response_model=MessageResponse, summary="手动触发数据更新")
def trigger_update(
    update_type: str = Query("all", description="更新类型: all, funds, nav, holdings"),
    db: Session = Depends(get_db)
):
    """
    手动触发数据更新任务
    
    - all: 全量更新（基金列表、净值、持仓）
    - funds: 仅更新基金列表
    - nav: 仅更新净值
    - holdings: 仅更新持仓
    """
    service = FundService(db)
    
    try:
        if update_type == "all":
            result = service.update_all_data()
            return MessageResponse(
                message=f"全量更新完成",
                success=True
            )
        elif update_type == "funds":
            result = service.update_fund_data()
            return MessageResponse(
                message=f"基金列表更新完成: 共 {result['total']} 条，新增 {result['new']} 条，更新 {result['updated']} 条",
                success=True
            )
        elif update_type == "nav":
            result = service.update_fund_nav()
            return MessageResponse(
                message=f"净值更新完成: 共 {result['total']} 只，更新 {result['updated']} 只",
                success=True
            )
        elif update_type == "holdings":
            result = service.update_fund_holdings()
            return MessageResponse(
                message=f"持仓更新完成: 更新 {result['funds_updated']} 只基金，共 {result['holdings_count']} 条持仓记录",
                success=True
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail={
                    "error_code": "INVALID_UPDATE_TYPE",
                    "message": f"无效的更新类型: {update_type}",
                    "details": {"valid_types": ["all", "funds", "nav", "holdings"]}
                }
            )
    except FundShowException as e:
        raise_http_exception(e)
    except Exception as e:
        logger.error(f"更新失败: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "UPDATE_FAILED",
                "message": f"更新失败: {str(e)}",
                "details": {}
            }
        )
