import akshare as ak
import pandas as pd
from typing import List, Dict, Optional, Callable, Any, TypeVar
from datetime import date
from functools import wraps
import time
import logging

from repo.config import get_settings
from repo.exceptions import DataFetchError, InvalidParameterError

logger = logging.getLogger(__name__)
settings = get_settings()

T = TypeVar('T')


def with_retry(
    max_retries: int = settings.MAX_RETRIES,
    delay: int = settings.RETRY_DELAY_SECONDS
) -> Callable:
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"{func.__name__} 执行失败，第 {attempt + 1} 次重试: {str(e)}"
                        )
                        time.sleep(delay * (attempt + 1))
                    else:
                        logger.error(f"{func.__name__} 执行失败，已达到最大重试次数: {str(e)}")
            raise DataFetchError(
                message=f"{func.__name__} 执行失败，已达到最大重试次数",
                source=func.__name__,
                details={"max_retries": max_retries, "error": str(last_exception)}
            )
        return wrapper
    return decorator


class OverseasFundDataFetcher:
    OVERSEAS_KEYWORDS = settings.overseas_keywords_list

    @classmethod
    def is_overseas_fund(cls, fund_name: str, fund_type: str = '') -> bool:
        if not fund_name:
            return False
        fund_info = f"{fund_name} {fund_type}".upper()
        return any(keyword.upper() in fund_info for keyword in cls.OVERSEAS_KEYWORDS)

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        if pd.isna(value) or value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _safe_date(value: Any) -> Optional[date]:
        if pd.isna(value) or value is None:
            return None
        try:
            dt = pd.to_datetime(value, errors='coerce')
            return dt.date() if pd.notna(dt) else None
        except Exception:
            return None

    @staticmethod
    def _safe_str(value: Any) -> str:
        if pd.isna(value) or value is None:
            return ''
        return str(value).strip()

    @with_retry()
    def _fetch_qdii_fund_list_raw(self) -> pd.DataFrame:
        df = ak.fund_etf_category_sina(symbol=settings.QDII_FUND_SYMBOL)
        if df is None or df.empty:
            raise DataFetchError(
                message=f"{settings.QDII_FUND_SYMBOL}列表为空",
                source="ak.fund_etf_category_sina"
            )
        return df

    def fetch_qdii_fund_list(self) -> pd.DataFrame:
        try:
            df = self._fetch_qdii_fund_list_raw()
            result_df = pd.DataFrame()
            result_df['fund_code'] = df['代码'].astype(str).str.strip()
            result_df['fund_name'] = df['名称'].astype(str).str.strip()
            result_df['unit_nav'] = pd.to_numeric(df['最新净值'], errors='coerce')
            result_df['accumulated_nav'] = pd.to_numeric(df['累计净值'], errors='coerce')
            result_df['nav_date'] = pd.to_datetime(df['日期'], errors='coerce')
            return result_df
        except DataFetchError:
            raise
        except Exception as e:
            logger.error(f"处理QDII基金列表失败: {e}")
            raise DataFetchError(
                message="处理QDII基金列表数据失败",
                source="fetch_qdii_fund_list",
                details={"error": str(e)}
            ) from e

    @with_retry()
    def _fetch_all_funds_raw(self) -> pd.DataFrame:
        df = ak.fund_name_em()
        if df is None or df.empty:
            raise DataFetchError(
                message="全部基金列表为空",
                source="ak.fund_name_em"
            )
        return df

    def fetch_overseas_fund_list(self) -> List[Dict[str, Any]]:
        funds: Dict[str, Dict[str, Any]] = {}

        try:
            qdii_df = self.fetch_qdii_fund_list()
            if not qdii_df.empty:
                for _, row in qdii_df.iterrows():
                    fund_code = self._safe_str(row['fund_code'])
                    if fund_code and fund_code not in funds:
                        funds[fund_code] = {
                            'fund_code': fund_code,
                            'fund_name': self._safe_str(row['fund_name']),
                            'fund_type': 'QDII',
                            'unit_nav': self._safe_float(row['unit_nav']),
                            'accumulated_nav': self._safe_float(row['accumulated_nav']),
                            'nav_date': self._safe_date(row['nav_date']),
                        }
            logger.info(f"从QDII列表获取了 {len(funds)} 只基金")
        except DataFetchError as e:
            logger.warning(f"获取QDII基金列表失败，继续从其他来源获取: {e.message}")

        try:
            all_funds_df = self._fetch_all_funds_raw()
            added_count = 0
            for _, row in all_funds_df.iterrows():
                fund_name = self._safe_str(row.get('基金简称'))
                fund_type = self._safe_str(row.get('基金类型'))

                if self.is_overseas_fund(fund_name, fund_type):
                    fund_code = self._safe_str(row.get('基金代码'))
                    if fund_code and fund_code not in funds:
                        funds[fund_code] = {
                            'fund_code': fund_code,
                            'fund_name': fund_name,
                            'fund_type': fund_type,
                            'fund_manager': self._safe_str(row.get('基金经理')),
                            'fund_company': self._safe_str(row.get('基金公司')),
                            'establish_date': self._safe_date(row.get('成立日期')),
                        }
                        added_count += 1
            logger.info(f"从全部基金列表新增了 {added_count} 只海外基金")
        except DataFetchError as e:
            logger.warning(f"获取全部基金列表失败: {e.message}")

        logger.info(f"共获取 {len(funds)} 只海外投资基金")
        return list(funds.values())

    @with_retry()
    def _fetch_fund_nav_raw(self, fund_code: str) -> pd.DataFrame:
        if not fund_code or not isinstance(fund_code, str):
            raise InvalidParameterError(
                param_name="fund_code",
                reason="基金代码必须是非空字符串"
            )
        df = ak.fund_etf_fund_info_em(fund=fund_code)
        if df is None or df.empty:
            raise DataFetchError(
                message=f"基金 {fund_code} 净值数据为空",
                source="ak.fund_etf_fund_info_em",
                details={"fund_code": fund_code}
            )
        return df

    def fetch_fund_nav(self, fund_code: str) -> Optional[Dict[str, Any]]:
        try:
            nav_df = self._fetch_fund_nav_raw(fund_code)
            latest = nav_df.iloc[0]
            return {
                'fund_code': fund_code,
                'unit_nav': self._safe_float(latest.get('单位净值')),
                'accumulated_nav': self._safe_float(latest.get('累计净值')),
                'nav_date': self._safe_date(latest.get('净值日期')),
            }
        except (DataFetchError, InvalidParameterError) as e:
            logger.warning(f"获取基金 {fund_code} 净值失败: {e.message}")
            return None
        except Exception as e:
            logger.error(f"处理基金 {fund_code} 净值数据异常: {e}")
            return None

    @with_retry()
    def _fetch_fund_holdings_raw(
        self,
        fund_code: str,
        year: str = settings.HOLDINGS_YEAR
    ) -> pd.DataFrame:
        if not fund_code or not isinstance(fund_code, str):
            raise InvalidParameterError(
                param_name="fund_code",
                reason="基金代码必须是非空字符串"
            )
        df = ak.fund_portfolio_em(code=fund_code, year=year)
        if df is None:
            return pd.DataFrame()
        return df

    def fetch_fund_holdings(
        self,
        fund_code: str,
        year: str = settings.HOLDINGS_YEAR
    ) -> List[Dict[str, Any]]:
        holdings: List[Dict[str, Any]] = []
        try:
            holdings_df = self._fetch_fund_holdings_raw(fund_code, year)
            if holdings_df.empty:
                return holdings

            for _, row in holdings_df.iterrows():
                holding = {
                    'fund_code': fund_code,
                    'stock_code': self._safe_str(row.get('股票代码')),
                    'stock_name': self._safe_str(row.get('股票名称')),
                    'holding_ratio': self._safe_float(row.get('占净值比例')),
                    'holding_shares': self._safe_float(row.get('持股数')),
                    'holding_value': self._safe_float(row.get('持仓市值')),
                    'report_date': self._safe_date(row.get('季度')),
                }
                if holding['stock_code'] or holding['stock_name']:
                    holdings.append(holding)

            logger.debug(f"获取基金 {fund_code} 持仓 {len(holdings)} 条")
        except (DataFetchError, InvalidParameterError) as e:
            logger.warning(f"获取基金 {fund_code} 持仓失败: {e.message}")
        except Exception as e:
            logger.error(f"处理基金 {fund_code} 持仓数据异常: {e}")

        return holdings

    def update_all_fund_nav(
        self,
        fund_codes: List[str],
        batch_size: int = settings.BATCH_SIZE
    ) -> Dict[str, Dict[str, Any]]:
        nav_data: Dict[str, Dict[str, Any]] = {}
        total = len(fund_codes)
        success = 0

        logger.info(f"开始更新 {total} 只基金的净值数据，批量大小: {batch_size}")

        for i, code in enumerate(fund_codes, 1):
            nav = self.fetch_fund_nav(code)
            if nav:
                nav_data[code] = nav
                success += 1

            if i % batch_size == 0:
                logger.info(f"净值更新进度: {i}/{total}, 成功: {success}")

        logger.info(f"净值更新完成: 总计 {total}, 成功 {success}, 失败 {total - success}")
        return nav_data
