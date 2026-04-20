from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime
import logging
from repo.models import Fund, FundHolding
from repo.data_fetcher import OverseasFundDataFetcher
from repo.exceptions import FundNotFoundException, DatabaseException, DataFetchException
from repo.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class FundService:
    """基金服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.fetcher = OverseasFundDataFetcher()
        self.default_limit = settings.DEFAULT_PAGE_SIZE
        self.max_limit = settings.MAX_PAGE_SIZE
        self.holdings_default_limit = settings.DATA_FETCH_HOLDINGS_DEFAULT_LIMIT
    
    def get_fund_list(self, skip: int = None, limit: int = None, fund_type: Optional[str] = None) -> tuple:
        """
        获取基金列表
        
        Args:
            skip: 跳过的记录数
            limit: 返回的记录数
            fund_type: 基金类型筛选
            
        Returns:
            (总数, 基金列表)
        """
        if skip is None:
            skip = settings.DEFAULT_SKIP
        if limit is None:
            limit = self.default_limit
        
        # 确保不超过最大限制
        limit = min(limit, self.max_limit)
        
        try:
            query = self.db.query(Fund)
            
            if fund_type:
                query = query.filter(Fund.fund_type.ilike(f"%{fund_type}%"))
            
            total = query.count()
            funds = query.order_by(Fund.updated_at.desc()).offset(skip).limit(limit).all()
            
            return total, funds
        except Exception as e:
            logger.error(f"获取基金列表失败: {e}")
            raise DatabaseException(
                message=f"获取基金列表失败: {str(e)}",
                operation="get_fund_list"
            )
    
    def get_fund_by_code(self, fund_code: str) -> Optional[Fund]:
        """
        通过基金代码获取基金
        
        Args:
            fund_code: 基金代码
            
        Returns:
            基金对象或None
        """
        try:
            return self.db.query(Fund).filter(Fund.fund_code == fund_code).first()
        except Exception as e:
            logger.error(f"获取基金 {fund_code} 失败: {e}")
            raise DatabaseException(
                message=f"获取基金 {fund_code} 失败: {str(e)}",
                operation="get_fund_by_code",
                details={"fund_code": fund_code}
            )
    
    def get_fund_or_raise(self, fund_code: str) -> Fund:
        """
        获取基金，如果不存在则抛出异常
        
        Args:
            fund_code: 基金代码
            
        Returns:
            基金对象
            
        Raises:
            FundNotFoundException: 基金不存在
        """
        fund = self.get_fund_by_code(fund_code)
        if not fund:
            raise FundNotFoundException(fund_code)
        return fund
    
    def get_fund_holdings(self, fund_code: str) -> List[FundHolding]:
        """
        获取基金持仓
        
        Args:
            fund_code: 基金代码
            
        Returns:
            持仓列表
        """
        try:
            return self.db.query(FundHolding).filter(
                FundHolding.fund_code == fund_code
            ).order_by(FundHolding.holding_ratio.desc().nullslast()).all()
        except Exception as e:
            logger.error(f"获取基金 {fund_code} 持仓失败: {e}")
            raise DatabaseException(
                message=f"获取基金 {fund_code} 持仓失败: {str(e)}",
                operation="get_fund_holdings",
                details={"fund_code": fund_code}
            )
    
    def update_fund_data(self) -> Dict:
        """
        更新基金数据
        
        Returns:
            更新结果统计
        """
        logger.info("开始更新基金数据...")
        
        try:
            funds_data = self.fetcher.fetch_overseas_fund_list()
        except DataFetchException as e:
            logger.error(f"获取基金列表数据失败: {e.message}")
            raise
        
        updated_count = 0
        new_count = 0
        error_count = 0
        
        try:
            for fund_data in funds_data:
                try:
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
                except Exception as e:
                    logger.error(f"处理基金 {fund_data.get('fund_code')} 时出错: {e}")
                    error_count += 1
                    continue
            
            self.db.commit()
            logger.info(f"基金数据更新完成: 新增 {new_count} 条, 更新 {updated_count} 条, 错误 {error_count} 条")
            
            return {
                "total": len(funds_data),
                "new": new_count,
                "updated": updated_count,
                "error": error_count
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新基金数据失败: {e}")
            raise DatabaseException(
                message=f"更新基金数据失败: {str(e)}",
                operation="update_fund_data"
            )
    
    def update_fund_nav(self) -> Dict:
        """
        更新基金净值
        
        Returns:
            更新结果统计
        """
        logger.info("开始更新基金净值...")
        
        try:
            funds = self.db.query(Fund).all()
            fund_codes = [f.fund_code for f in funds]
        except Exception as e:
            logger.error(f"获取基金列表失败: {e}")
            raise DatabaseException(
                message=f"获取基金列表失败: {str(e)}",
                operation="update_fund_nav"
            )
        
        try:
            nav_data = self.fetcher.update_all_fund_nav(fund_codes)
        except Exception as e:
            logger.error(f"获取净值数据失败: {e}")
            raise DataFetchException(
                message=f"获取净值数据失败: {str(e)}",
                source="update_all_fund_nav"
            )
        
        updated_count = 0
        error_count = 0
        
        try:
            for code, nav in nav_data.items():
                try:
                    fund = self.get_fund_by_code(code)
                    if fund:
                        fund.unit_nav = nav.get('unit_nav')
                        fund.accumulated_nav = nav.get('accumulated_nav')
                        fund.nav_date = nav.get('nav_date')
                        fund.updated_at = datetime.utcnow()
                        updated_count += 1
                except Exception as e:
                    logger.error(f"更新基金 {code} 净值时出错: {e}")
                    error_count += 1
                    continue
            
            self.db.commit()
            logger.info(f"基金净值更新完成: 更新 {updated_count} 条, 错误 {error_count} 条")
            
            return {
                "total": len(fund_codes),
                "updated": updated_count,
                "error": error_count
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新基金净值失败: {e}")
            raise DatabaseException(
                message=f"更新基金净值失败: {str(e)}",
                operation="update_fund_nav"
            )
    
    def update_fund_holdings(self, fund_code: Optional[str] = None) -> Dict:
        """
        更新基金持仓数据
        
        Args:
            fund_code: 指定基金代码，为None则更新前N只基金（N由配置决定）
            
        Returns:
            更新结果统计
        """
        logger.info("开始更新基金持仓数据...")
        
        try:
            if fund_code:
                fund = self.get_fund_by_code(fund_code)
                if not fund:
                    raise FundNotFoundException(fund_code)
                funds = [fund]
            else:
                funds = self.db.query(Fund).limit(self.holdings_default_limit).all()
        except FundNotFoundException:
            raise
        except Exception as e:
            logger.error(f"获取基金列表失败: {e}")
            raise DatabaseException(
                message=f"获取基金列表失败: {str(e)}",
                operation="update_fund_holdings"
            )
        
        total_holdings = 0
        updated_funds = 0
        error_funds = 0
        
        try:
            for fund in funds:
                try:
                    holdings_data = self.fetcher.fetch_fund_holdings(fund.fund_code)
                    
                    if holdings_data:
                        # 删除旧持仓
                        self.db.query(FundHolding).filter(
                            FundHolding.fund_code == fund.fund_code
                        ).delete()
                        
                        # 添加新持仓
                        for holding_data in holdings_data:
                            holding = FundHolding(**holding_data)
                            self.db.add(holding)
                            total_holdings += 1
                        
                        updated_funds += 1
                except DataFetchException as e:
                    logger.warning(f"获取基金 {fund.fund_code} 持仓失败: {e.message}")
                    error_funds += 1
                    continue
                except Exception as e:
                    logger.error(f"更新基金 {fund.fund_code} 持仓时出错: {e}")
                    error_funds += 1
                    continue
            
            self.db.commit()
            logger.info(f"基金持仓更新完成: 更新 {updated_funds} 只基金, 共 {total_holdings} 条持仓记录, 错误 {error_funds} 只基金")
            
            return {
                "funds_updated": updated_funds,
                "holdings_count": total_holdings,
                "funds_error": error_funds
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新基金持仓失败: {e}")
            raise DatabaseException(
                message=f"更新基金持仓失败: {str(e)}",
                operation="update_fund_holdings"
            )
    
    def update_all_data(self) -> Dict:
        """
        全量更新所有数据
        
        Returns:
            更新结果统计
        """
        logger.info("开始全量更新数据...")
        
        fund_result = self.update_fund_data()
        nav_result = self.update_fund_nav()
        holdings_result = self.update_fund_holdings()
        
        return {
            "funds": fund_result,
            "nav": nav_result,
            "holdings": holdings_result
        }
