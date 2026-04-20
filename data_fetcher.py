import akshare as ak
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class OverseasFundDataFetcher:
    
    def __init__(self):
        self.overseas_keywords = [
            'QDII', 'QDII-ETF', '海外', '港股', '美股', '纳斯达克', 
            '标普', '恒生', '中概', '全球', '国际', '境外', '沪港深',
            '香港', '美国', '欧洲', '日本', '新兴市场'
        ]
    
    def is_overseas_fund(self, fund_name: str, fund_type: str = '') -> bool:
        if not fund_name:
            return False
        fund_info = f"{fund_name} {fund_type}".upper()
        for keyword in self.overseas_keywords:
            if keyword.upper() in fund_info:
                return True
        return False
    
    def fetch_qdii_fund_list(self) -> pd.DataFrame:
        try:
            df = ak.fund_etf_category_sina(symbol="QDII基金")
            if df is not None and not df.empty:
                df['fund_code'] = df['代码'].astype(str)
                df['fund_name'] = df['名称']
                df['unit_nav'] = pd.to_numeric(df['最新净值'], errors='coerce')
                df['accumulated_nav'] = pd.to_numeric(df['累计净值'], errors='coerce')
                df['nav_date'] = pd.to_datetime(df['日期'], errors='coerce')
                return df[['fund_code', 'fund_name', 'unit_nav', 'accumulated_nav', 'nav_date']]
        except Exception as e:
            logger.error(f"获取QDII基金列表失败: {e}")
        return pd.DataFrame()
    
    def fetch_overseas_fund_list(self) -> List[Dict]:
        funds = []
        
        qdii_df = self.fetch_qdii_fund_list()
        if not qdii_df.empty:
            for _, row in qdii_df.iterrows():
                fund = {
                    'fund_code': str(row['fund_code']),
                    'fund_name': str(row['fund_name']),
                    'fund_type': 'QDII',
                    'unit_nav': float(row['unit_nav']) if pd.notna(row['unit_nav']) else None,
                    'accumulated_nav': float(row['accumulated_nav']) if pd.notna(row['accumulated_nav']) else None,
                    'nav_date': row['nav_date'].date() if pd.notna(row['nav_date']) else None,
                }
                funds.append(fund)
        
        try:
            all_funds_df = ak.fund_name_em()
            if all_funds_df is not None and not all_funds_df.empty:
                for _, row in all_funds_df.iterrows():
                    fund_name = str(row.get('基金简称', ''))
                    fund_type = str(row.get('基金类型', ''))
                    
                    if self.is_overseas_fund(fund_name, fund_type):
                        fund_code = str(row.get('基金代码', ''))
                        existing_codes = [f['fund_code'] for f in funds]
                        if fund_code not in existing_codes:
                            fund = {
                                'fund_code': fund_code,
                                'fund_name': fund_name,
                                'fund_type': fund_type,
                                'fund_manager': str(row.get('基金经理', '')),
                                'fund_company': str(row.get('基金公司', '')),
                                'establish_date': pd.to_datetime(row.get('成立日期', ''), errors='coerce').date() if pd.notna(row.get('成立日期')) else None,
                            }
                            funds.append(fund)
        except Exception as e:
            logger.error(f"获取全部基金列表失败: {e}")
        
        logger.info(f"共获取 {len(funds)} 只海外投资基金")
        return funds
    
    def fetch_fund_nav(self, fund_code: str) -> Optional[Dict]:
        try:
            nav_df = ak.fund_etf_fund_info_em(fund=fund_code)
            if nav_df is not None and not nav_df.empty:
                latest = nav_df.iloc[0]
                return {
                    'fund_code': fund_code,
                    'unit_nav': float(latest.get('单位净值', 0)),
                    'accumulated_nav': float(latest.get('累计净值', 0)),
                    'nav_date': pd.to_datetime(latest.get('净值日期'), errors='coerce').date() if pd.notna(latest.get('净值日期')) else None,
                }
        except Exception as e:
            logger.error(f"获取基金 {fund_code} 净值失败: {e}")
        return None
    
    def fetch_fund_holdings(self, fund_code: str) -> List[Dict]:
        holdings = []
        try:
            holdings_df = ak.fund_portfolio_em(code=fund_code, year="2024")
            if holdings_df is not None and not holdings_df.empty:
                for _, row in holdings_df.iterrows():
                    holding = {
                        'fund_code': fund_code,
                        'stock_code': str(row.get('股票代码', '')),
                        'stock_name': str(row.get('股票名称', '')),
                        'holding_ratio': float(row.get('占净值比例', 0)) if pd.notna(row.get('占净值比例')) else None,
                        'holding_shares': float(row.get('持股数', 0)) if pd.notna(row.get('持股数')) else None,
                        'holding_value': float(row.get('持仓市值', 0)) if pd.notna(row.get('持仓市值')) else None,
                        'report_date': pd.to_datetime(row.get('季度', ''), errors='coerce').date() if pd.notna(row.get('季度')) else None,
                    }
                    holdings.append(holding)
        except Exception as e:
            logger.error(f"获取基金 {fund_code} 持仓失败: {e}")
        
        return holdings
    
    def update_all_fund_nav(self, fund_codes: List[str]) -> Dict[str, Dict]:
        nav_data = {}
        for code in fund_codes:
            nav = self.fetch_fund_nav(code)
            if nav:
                nav_data[code] = nav
        return nav_data
