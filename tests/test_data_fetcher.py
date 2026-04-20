import pytest
import pandas as pd
from unittest.mock import Mock, patch
from repo.data_fetcher import (
    OverseasFundDataFetcher,
    retry_on_failure,
    safe_numeric_convert,
    safe_date_convert,
)
from repo.exceptions import DataFetchException


class TestDataFetcherUtils:
    """测试数据获取工具函数"""
    
    def test_safe_numeric_convert_valid(self):
        """测试安全数值转换-有效值"""
        assert safe_numeric_convert("123.45") == 123.45
        assert safe_numeric_convert(100) == 100.0
        assert safe_numeric_convert(0) == 0.0
    
    def test_safe_numeric_convert_invalid(self):
        """测试安全数值转换-无效值"""
        assert safe_numeric_convert(None) is None
        assert safe_numeric_convert("") is None
        assert safe_numeric_convert("abc") is None
        assert safe_numeric_convert(float('nan')) is None
    
    def test_safe_numeric_convert_with_default(self):
        """测试安全数值转换-默认值"""
        assert safe_numeric_convert(None, default=0.0) == 0.0
        assert safe_numeric_convert("invalid", default=-1.0) == -1.0
    
    def test_safe_date_convert_valid(self):
        """测试安全日期转换-有效值"""
        result = safe_date_convert("2024-01-15")
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
    
    def test_safe_date_convert_invalid(self):
        """测试安全日期转换-无效值"""
        assert safe_date_convert(None) is None
        assert safe_date_convert("") is None
        assert safe_date_convert("invalid") is None
    
    def test_retry_on_failure_success(self):
        """测试重试装饰器-成功"""
        mock_func = Mock(return_value="success")
        
        @retry_on_failure(max_retries=3, delay=0.1)
        def test_func():
            return mock_func()
        
        result = test_func()
        assert result == "success"
        assert mock_func.call_count == 1
    
    def test_retry_on_failure_eventual_success(self):
        """测试重试装饰器-最终成功"""
        mock_func = Mock(side_effect=[Exception("error"), "success"])
        
        @retry_on_failure(max_retries=3, delay=0.1)
        def test_func():
            return mock_func()
        
        result = test_func()
        assert result == "success"
        assert mock_func.call_count == 2
    
    def test_retry_on_failure_all_fail(self):
        """测试重试装饰器-全部失败"""
        mock_func = Mock(side_effect=Exception("always fails"))
        
        @retry_on_failure(max_retries=2, delay=0.1)
        def test_func():
            return mock_func()
        
        with pytest.raises(Exception):
            test_func()
        assert mock_func.call_count == 2


class TestOverseasFundDataFetcher:
    """测试海外基金数据获取器"""
    
    @pytest.fixture
    def fetcher(self):
        return OverseasFundDataFetcher()
    
    def test_init(self, fetcher):
        """测试初始化"""
        assert len(fetcher.overseas_keywords) > 0
        assert "QDII" in fetcher.overseas_keywords
        assert "海外" in fetcher.overseas_keywords
    
    def test_is_overseas_fund_true(self, fetcher):
        """测试判断海外基金-是"""
        assert fetcher.is_overseas_fund("某某QDII基金") is True
        assert fetcher.is_overseas_fund("某某海外基金") is True
        assert fetcher.is_overseas_fund("某某基金", "QDII") is True
    
    def test_is_overseas_fund_false(self, fetcher):
        """测试判断海外基金-否"""
        assert fetcher.is_overseas_fund("某某货币基金") is False
        assert fetcher.is_overseas_fund("某某债券基金") is False
        assert fetcher.is_overseas_fund("") is False
        assert fetcher.is_overseas_fund(None) is False
    
    @patch('repo.data_fetcher.ak.fund_etf_category_sina')
    def test_fetch_qdii_fund_list_success(self, mock_ak, fetcher):
        """测试获取QDII基金列表-成功"""
        mock_data = pd.DataFrame({
            '代码': ['000001', '000002'],
            '名称': ['基金A', '基金B'],
            '最新净值': ['1.5', '2.0'],
            '累计净值': ['2.5', '3.0'],
            '日期': ['2024-01-15', '2024-01-15']
        })
        mock_ak.return_value = mock_data
        
        result = fetcher.fetch_qdii_fund_list()
        
        assert len(result) == 2
        assert result.iloc[0]['fund_code'] == '000001'
        assert result.iloc[0]['fund_name'] == '基金A'
    
    @patch('repo.data_fetcher.ak.fund_etf_category_sina')
    def test_fetch_qdii_fund_list_empty(self, mock_ak, fetcher):
        """测试获取QDII基金列表-空数据"""
        mock_ak.return_value = pd.DataFrame()
        
        result = fetcher.fetch_qdii_fund_list()
        
        assert result.empty
    
    @patch('repo.data_fetcher.ak.fund_etf_category_sina')
    def test_fetch_qdii_fund_list_exception(self, mock_ak, fetcher):
        """测试获取QDII基金列表-异常"""
        mock_ak.side_effect = Exception("API错误")
        
        with pytest.raises(DataFetchException) as exc_info:
            fetcher.fetch_qdii_fund_list()
        
        assert exc_info.value.error_code == "DATA_FETCH_ERROR"
    
    @patch('repo.data_fetcher.ak.fund_name_em')
    @patch.object(OverseasFundDataFetcher, 'fetch_qdii_fund_list')
    def test_fetch_overseas_fund_list(self, mock_qdii, mock_all, fetcher):
        """测试获取海外基金列表"""
        mock_qdii.return_value = pd.DataFrame()
        
        mock_all_data = pd.DataFrame({
            '基金代码': ['000001', '000002'],
            '基金简称': ['QDII基金A', '债券基金B'],
            '基金类型': ['QDII', '债券型'],
            '基金经理': ['经理A', '经理B'],
            '基金公司': ['公司A', '公司B'],
            '成立日期': ['2020-01-01', '2021-01-01']
        })
        mock_all.return_value = mock_all_data
        
        result = fetcher.fetch_overseas_fund_list()
        
        assert len(result) == 1
        assert result[0]['fund_code'] == '000001'
        assert result[0]['fund_type'] == 'QDII'
    
    @patch('repo.data_fetcher.ak.fund_etf_fund_info_em')
    def test_fetch_fund_nav_success(self, mock_ak, fetcher):
        """测试获取基金净值-成功"""
        mock_data = pd.DataFrame({
            '单位净值': ['1.5'],
            '累计净值': ['2.5'],
            '净值日期': ['2024-01-15']
        })
        mock_ak.return_value = mock_data
        
        result = fetcher.fetch_fund_nav("000001")
        
        assert result is not None
        assert result['fund_code'] == '000001'
        assert result['unit_nav'] == 1.5
        assert result['accumulated_nav'] == 2.5
    
    @patch('repo.data_fetcher.ak.fund_etf_fund_info_em')
    def test_fetch_fund_nav_empty(self, mock_ak, fetcher):
        """测试获取基金净值-空数据"""
        mock_ak.return_value = pd.DataFrame()
        
        result = fetcher.fetch_fund_nav("000001")
        
        assert result is None
    
    def test_fetch_fund_nav_empty_code(self, fetcher):
        """测试获取基金净值-空代码"""
        result = fetcher.fetch_fund_nav("")
        assert result is None
        
        result = fetcher.fetch_fund_nav(None)
        assert result is None
    
    @patch('repo.data_fetcher.ak.fund_portfolio_em')
    def test_fetch_fund_holdings_success(self, mock_ak, fetcher):
        """测试获取基金持仓-成功"""
        mock_data = pd.DataFrame({
            '股票代码': ['00700', '09988'],
            '股票名称': ['腾讯', '阿里'],
            '占净值比例': ['10.5', '8.5'],
            '持股数': ['1000', '2000'],
            '持仓市值': ['500000', '400000'],
            '季度': ['2024Q1', '2024Q1']
        })
        mock_ak.return_value = mock_data
        
        result = fetcher.fetch_fund_holdings("000001")
        
        assert len(result) == 2
        assert result[0]['stock_code'] == '00700'
        assert result[0]['stock_name'] == '腾讯'
        assert result[0]['holding_ratio'] == 10.5
    
    @patch('repo.data_fetcher.ak.fund_portfolio_em')
    def test_fetch_fund_holdings_empty(self, mock_ak, fetcher):
        """测试获取基金持仓-空数据"""
        mock_ak.return_value = pd.DataFrame()
        
        result = fetcher.fetch_fund_holdings("000001")
        
        assert result == []
    
    def test_fetch_fund_holdings_empty_code(self, fetcher):
        """测试获取基金持仓-空代码"""
        result = fetcher.fetch_fund_holdings("")
        assert result == []
