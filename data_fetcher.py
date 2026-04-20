import akshare as ak
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime
import logging
import time
from functools import wraps
from repo.exceptions import DataFetchException, ExternalAPIException
from repo.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def retry_on_failure(max_retries: int = None, delay: float = None):
    """重试装饰器"""
    if max_retries is None:
        max_retries = settings.DATA_FETCH_MAX_RETRIES
    if delay is None:
        delay = settings.DATA_FETCH_RETRY_DELAY
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (2 ** attempt)
                        logger.warning(f"{func.__name__} 第 {attempt + 1} 次尝试失败，{wait_time}秒后重试: {e}")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"{func.__name__} 所有 {max_retries} 次尝试都失败")
            raise last_exception
        return wrapper
    return decorator


def safe_numeric_convert(value, default=None):
    """安全地将值转换为数值类型"""
    if pd.isna(value) or value is None or value == '':
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_date_convert(value, default=None):
    """安全地将值转换为日期类型"""
    if pd.isna(value) or value is None or value == '':
        return default
    try:
        return pd.to_datetime(value, errors='coerce').date()
    except (ValueError, TypeError):
        return default


class OverseasFundDataFetcher:
    """海外基金数据获取器"""
    
    def __init__(self):
        self.overseas_keywords = settings.OVERSEAS_FUND_KEYWORDS
        self.qdii_symbol = settings.QDII_FUND_SYMBOL
        self.batch_delay = settings.DATA_FETCH_BATCH_DELAY
    
    def is_overseas_fund(self, fund_name: str, fund_type: str = '') -> bool:
        """判断是否为海外基金"""
        if not fund_name:
            return False
        fund_info = f"{fund_name} {fund_type}".upper()
        return any(keyword.upper() in fund_info for keyword in self.overseas_keywords)
    
    @retry_on_failure()
    def fetch_qdii_fund_list(self) -> pd.DataFrame:
        """获取QDII基金列表"""
        try:
            df = ak.fund_etf_category_sina(symbol=self.qdii_symbol)
            if df is None or df.empty:
                logger.warning("获取QDII基金列表返回空数据")
                return pd.DataFrame()
            
            column_mapping = {
                'fund_code': '代码',
                'fund_name': '名称',
                'unit_nav': '最新净值',
                'accumulated_nav': '累计净值',
                'nav_date': '日期'
            }
            
            result_df = pd.DataFrame()
            for new_col, old_col in column_mapping.items():
                if old_col in df.columns:
                    result_df[new_col] = df[old_col]
            
            if 'fund_code' in result_df.columns:
                result_df['fund_code'] = result_df['fund_code'].astype(str)
            if 'unit_nav' in result_df.columns:
                result_df['unit_nav'] = pd.to_numeric(result_df['unit_nav'], errors='coerce')
            if 'accumulated_nav' in result_df.columns:
                result_df['accumulated_nav'] = pd.to_numeric(result_df['accumulated_nav'], errors='coerce')
            if 'nav_date' in result_df.columns:
                result_df['nav_date'] = pd.to_datetime(result_df['nav_date'], errors='coerce')
            
            return result_df[['fund_code', 'fund_name', 'unit_nav', 'accumulated_nav', 'nav_date']]
            
        except Exception as e:
            logger.error(f"获取QDII基金列表失败: {e}")
            raise DataFetchException(
                message=f"获取QDII基金列表失败: {str(e)}",
                source="akshare.fund_etf_category_sina"
            )
    
    def fetch_overseas_fund_list(self) -> List[Dict]:
        """获取海外基金列表"""
        funds = []
        
        try:
            qdii_df = self.fetch_qdii_fund_list()
            if not qdii_df.empty:
                for _, row in qdii_df.iterrows():
                    fund = {
                        'fund_code': str(row['fund_code']),
                        'fund_name': str(row['fund_name']),
                        'fund_type': 'QDII',
                        'unit_nav': safe_numeric_convert(row.get('unit_nav')),
                        'accumulated_nav': safe_numeric_convert(row.get('accumulated_nav')),
                        'nav_date': safe_date_convert(row.get('nav_date')),
                    }
                    funds.append(fund)
        except DataFetchException as e:
            logger.warning(f"QDII基金列表获取失败，继续尝试其他来源: {e.message}")
        
        try:
            all_funds_df = ak.fund_name_em()
            if all_funds_df is None or all_funds_df.empty:
                logger.warning("获取全部基金列表返回空数据")
            else:
                existing_codes = {f['fund_code'] for f in funds}
                
                for _, row in all_funds_df.iterrows():
                    fund_name = str(row.get('基金简称', ''))
                    fund_type = str(row.get('基金类型', ''))
                    
                    if self.is_overseas_fund(fund_name, fund_type):
                        fund_code = str(row.get('基金代码', ''))
                        if fund_code and fund_code not in existing_codes:
                            establish_date = row.get('成立日期')
                            fund = {
                                'fund_code': fund_code,
                                'fund_name': fund_name,
                                'fund_type': fund_type,
                                'fund_manager': str(row.get('基金经理', '')) if pd.notna(row.get('基金经理')) else None,
                                'fund_company': str(row.get('基金公司', '')) if pd.notna(row.get('基金公司')) else None,
                                'establish_date': safe_date_convert(establish_date),
                            }
                            funds.append(fund)
                            existing_codes.add(fund_code)
                            
        except Exception as e:
            logger.error(f"获取全部基金列表失败: {e}")
            raise DataFetchException(
                message=f"获取全部基金列表失败: {str(e)}",
                source="akshare.fund_name_em"
            )
        
        logger.info(f"共获取 {len(funds)} 只海外投资基金")
        return funds
    
    @retry_on_failure(max_retries=2, delay=0.5)
    def fetch_fund_nav(self, fund_code: str) -> Optional[Dict]:
        """获取基金净值"""
        if not fund_code:
            logger.warning("基金代码为空，跳过净值获取")
            return None
        
        try:
            nav_df = ak.fund_etf_fund_info_em(fund=fund_code)
            if nav_df is None or nav_df.empty:
                logger.warning(f"基金 {fund_code} 净值数据为空")
                return None
            
            latest = nav_df.iloc[0]
            
            unit_nav = safe_numeric_convert(latest.get('单位净值'))
            accumulated_nav = safe_numeric_convert(latest.get('累计净值'))
            nav_date = safe_date_convert(latest.get('净值日期'))
            
            if unit_nav is None:
                logger.warning(f"基金 {fund_code} 单位净值为空")
                return None
            
            return {
                'fund_code': fund_code,
                'unit_nav': unit_nav,
                'accumulated_nav': accumulated_nav,
                'nav_date': nav_date,
            }
            
        except Exception as e:
            logger.error(f"获取基金 {fund_code} 净值失败: {e}")
            raise DataFetchException(
                message=f"获取基金 {fund_code} 净值失败: {str(e)}",
                source="akshare.fund_etf_fund_info_em",
                details={"fund_code": fund_code}
            )
    
    @retry_on_failure(max_retries=2, delay=0.5)
    def fetch_fund_holdings(self, fund_code: str, year: str = None) -> List[Dict]:
        """获取基金持仓"""
        holdings = []
        
        if not fund_code:
            logger.warning("基金代码为空，跳过持仓获取")
            return holdings
        
        if year is None:
            year = settings.DATA_FETCH_HOLDINGS_DEFAULT_YEAR
        
        try:
            holdings_df = ak.fund_portfolio_em(code=fund_code, year=year)
            if holdings_df is None or holdings_df.empty:
                logger.warning(f"基金 {fund_code} 持仓数据为空")
                return holdings
            
            for _, row in holdings_df.iterrows():
                holding_ratio = safe_numeric_convert(row.get('占净值比例'))
                holding_shares = safe_numeric_convert(row.get('持股数'))
                holding_value = safe_numeric_convert(row.get('持仓市值'))
                
                holding = {
                    'fund_code': fund_code,
                    'stock_code': str(row.get('股票代码', '')) if pd.notna(row.get('股票代码')) else None,
                    'stock_name': str(row.get('股票名称', '')) if pd.notna(row.get('股票名称')) else None,
                    'holding_ratio': holding_ratio,
                    'holding_shares': holding_shares,
                    'holding_value': holding_value,
                    'report_date': safe_date_convert(row.get('季度')),
                }
                holdings.append(holding)
                
        except Exception as e:
            logger.error(f"获取基金 {fund_code} 持仓失败: {e}")
            raise DataFetchException(
                message=f"获取基金 {fund_code} 持仓失败: {str(e)}",
                source="akshare.fund_portfolio_em",
                details={"fund_code": fund_code, "year": year}
            )
        
        return holdings
    
    def update_all_fund_nav(self, fund_codes: List[str], batch_size: int = None) -> Dict[str, Dict]:
        """批量更新基金净值"""
        if batch_size is None:
            batch_size = settings.DATA_FETCH_BATCH_SIZE
        
        nav_data = {}
        total = len(fund_codes)
        
        for i in range(0, total, batch_size):
            batch = fund_codes[i:i + batch_size]
            logger.info(f"正在处理第 {i//batch_size + 1} 批净值数据 ({i+1}-{min(i+batch_size, total)}/{total})")
            
            for code in batch:
                try:
                    nav = self.fetch_fund_nav(code)
                    if nav:
                        nav_data[code] = nav
                except DataFetchException as e:
                    logger.warning(f"获取基金 {code} 净值失败，跳过: {e.message}")
                except Exception as e:
                    logger.error(f"获取基金 {code} 净值时发生未预期错误: {e}")
            
            if i + batch_size < total:
                time.sleep(self.batch_delay)
        
        logger.info(f"净值更新完成: 成功 {len(nav_data)}/{total}")
        return nav_data
