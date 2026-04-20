import pytest
from repo.exceptions import (
    FundShowException,
    DataFetchException,
    DatabaseException,
    FundNotFoundException,
    ValidationException,
    ExternalAPIException,
    raise_http_exception,
)
from fastapi import HTTPException


class TestExceptions:
    """测试自定义异常"""
    
    def test_base_exception(self):
        """测试基础异常"""
        exc = FundShowException("测试错误", "TEST_ERROR", {"key": "value"})
        assert exc.message == "测试错误"
        assert exc.error_code == "TEST_ERROR"
        assert exc.details == {"key": "value"}
        assert str(exc) == "测试错误"
    
    def test_data_fetch_exception(self):
        """测试数据获取异常"""
        exc = DataFetchException("获取失败", "test_source")
        assert exc.error_code == "DATA_FETCH_ERROR"
        assert exc.details["source"] == "test_source"
    
    def test_database_exception(self):
        """测试数据库异常"""
        exc = DatabaseException("操作失败", "insert")
        assert exc.error_code == "DATABASE_ERROR"
        assert exc.details["operation"] == "insert"
    
    def test_fund_not_found_exception(self):
        """测试基金不存在异常"""
        exc = FundNotFoundException("000001")
        assert exc.error_code == "FUND_NOT_FOUND"
        assert exc.details["fund_code"] == "000001"
        assert "000001" in exc.message
    
    def test_validation_exception(self):
        """测试验证异常"""
        exc = ValidationException("验证失败", "fund_code")
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.details["field"] == "fund_code"
    
    def test_external_api_exception(self):
        """测试外部API异常"""
        exc = ExternalAPIException("API错误", "akshare", 500)
        assert exc.error_code == "EXTERNAL_API_ERROR"
        assert exc.details["api_name"] == "akshare"
        assert exc.details["status_code"] == 500
    
    def test_raise_http_exception_fund_not_found(self):
        """测试基金不存在HTTP异常转换"""
        exc = FundNotFoundException("000001")
        with pytest.raises(HTTPException) as http_exc:
            raise_http_exception(exc)
        assert http_exc.value.status_code == 404
        assert http_exc.value.detail["error_code"] == "FUND_NOT_FOUND"
    
    def test_raise_http_exception_validation(self):
        """测试验证错误HTTP异常转换"""
        exc = ValidationException("验证失败")
        with pytest.raises(HTTPException) as http_exc:
            raise_http_exception(exc)
        assert http_exc.value.status_code == 400
        assert http_exc.value.detail["error_code"] == "VALIDATION_ERROR"
    
    def test_raise_http_exception_database(self):
        """测试数据库错误HTTP异常转换"""
        exc = DatabaseException("数据库错误")
        with pytest.raises(HTTPException) as http_exc:
            raise_http_exception(exc)
        assert http_exc.value.status_code == 500
        assert http_exc.value.detail["error_code"] == "DATABASE_ERROR"
