import pytest
import pandas as pd
from datetime import date

from repo.data_fetcher import OverseasFundDataFetcher, with_retry


class TestOverseasFundDataFetcher:
    def test_is_overseas_fund_with_qdii(self):
        assert OverseasFundDataFetcher.is_overseas_fund("华夏纳斯达克100ETF") is True
        assert OverseasFundDataFetcher.is_overseas_fund("易方达QDII基金") is True

    def test_is_overseas_fund_with_keywords(self):
        assert OverseasFundDataFetcher.is_overseas_fund("南方香港优选") is True
        assert OverseasFundDataFetcher.is_overseas_fund("广发美国房地产") is True

    def test_is_overseas_fund_without_keywords(self):
        assert OverseasFundDataFetcher.is_overseas_fund("华夏沪深300ETF") is False
        assert OverseasFundDataFetcher.is_overseas_fund("易方达消费精选") is False

    def test_is_overseas_fund_empty_name(self):
        assert OverseasFundDataFetcher.is_overseas_fund("") is False

    def test_safe_float_with_valid(self):
        assert OverseasFundDataFetcher._safe_float("1.234") == 1.234
        assert OverseasFundDataFetcher._safe_float(1.234) == 1.234

    def test_safe_float_with_invalid(self):
        assert OverseasFundDataFetcher._safe_float(None) is None
        assert OverseasFundDataFetcher._safe_float(pd.NA) is None
        assert OverseasFundDataFetcher._safe_float("invalid") is None

    def test_safe_str_with_valid(self):
        assert OverseasFundDataFetcher._safe_str("  test  ") == "test"
        assert OverseasFundDataFetcher._safe_str(123) == "123"

    def test_safe_str_with_invalid(self):
        assert OverseasFundDataFetcher._safe_str(None) == ""
        assert OverseasFundDataFetcher._safe_str(pd.NA) == ""

    def test_safe_date_with_valid(self):
        result = OverseasFundDataFetcher._safe_date("2024-01-01")
        assert result == date(2024, 1, 1)

    def test_safe_date_with_invalid(self):
        assert OverseasFundDataFetcher._safe_date(None) is None
        assert OverseasFundDataFetcher._safe_date("invalid") is None

    def test_fetcher_initialization(self):
        fetcher = OverseasFundDataFetcher()
        assert fetcher is not None

    def test_constants_defined(self):
        assert len(OverseasFundDataFetcher.OVERSEAS_KEYWORDS) > 0
        assert 'QDII' in OverseasFundDataFetcher.OVERSEAS_KEYWORDS
        assert '美股' in OverseasFundDataFetcher.OVERSEAS_KEYWORDS


class TestRetryDecorator:
    def test_with_retry_success_first_attempt(self):
        call_count = 0

        @with_retry(max_retries=3)
        def success_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = success_func()
        assert result == "success"
        assert call_count == 1

    def test_with_retry_success_after_retries(self):
        call_count = 0

        @with_retry(max_retries=2, delay=0)
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary error")
            return "success"

        result = flaky_func()
        assert result == "success"
        assert call_count == 3
