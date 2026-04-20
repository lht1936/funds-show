from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from repo.config import get_settings
from repo.database import get_db
from repo.services import FundService
from repo.exceptions import InvalidParameterError
from repo.schemas import (
    FundResponse,
    FundListResponse,
    FundDetailResponse,
    FundHoldingResponse,
    MessageResponse
)

settings = get_settings()

router = APIRouter(prefix="/api/v1/funds", tags=["funds"])


@router.get("", response_model=FundListResponse, summary="获取基金列表")
def get_fund_list(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(settings.DEFAULT_LIST_LIMIT, ge=1, le=settings.MAX_LIST_LIMIT, description="返回的记录数"),
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
    holdings = service.get_fund_holdings(fund_code)

    return [FundHoldingResponse.model_validate(h) for h in holdings]


@router.post("/update", response_model=MessageResponse, summary="手动触发数据更新")
def trigger_update(
    update_type: str = Query("all", description="更新类型: all, funds, nav, holdings"),
    db: Session = Depends(get_db)
):
    service = FundService(db)

    valid_types = ["all", "funds", "nav", "holdings"]
    if update_type not in valid_types:
        raise InvalidParameterError(
            param_name="update_type",
            reason=f"必须是以下值之一: {', '.join(valid_types)}"
        )

    results = {
        "all": service.update_all_data,
        "funds": service.update_fund_data,
        "nav": service.update_fund_nav,
        "holdings": service.update_fund_holdings
    }

    result = results[update_type]()

    messages = {
        "all": "全量更新完成",
        "funds": "基金列表更新完成",
        "nav": "净值更新完成",
        "holdings": "持仓更新完成"
    }

    return MessageResponse(
        message=f"{messages[update_type]}: {result}",
        success=True
    )
