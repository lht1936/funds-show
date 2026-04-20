import pytest
from fastapi import status
from repo.exceptions import (
    AppException,
    FundNotFoundError,
    DataFetchError,
    DatabaseError,
    ValidationError,
    UpdateError
)


class TestExceptions:
    
    def test_app_exception(self):
        exc = AppException(
            message="测试错误",
            error_code="TEST_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"key": "value"}
        )
        
        assert exc.message == "测试错误"
        assert exc.error_code == "TEST_ERROR"
        assert exc.status_code == status.HTTP_400_BAD_REQUEST
        assert exc.details == {"key": "value"}
    
    def test_fund_not_found_error(self):
        exc = FundNotFoundError("000001")
        
        assert exc.message == "基金 000001 不存在"
        assert exc.error_code == "FUND_NOT_FOUND"
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert exc.details["fund_code"] == "000001"
    
    def test_data_fetch_error(self):
        exc = DataFetchError("test_source", "获取数据失败")
        
        assert exc.message == "获取数据失败"
        assert exc.error_code == "DATA_FETCH_ERROR"
        assert exc.status_code == status.HTTP_502_BAD_GATEWAY
        assert exc.details["source"] == "test_source"
    
    def test_database_error(self):
        exc = DatabaseError("insert", "插入失败")
        
        assert exc.message == "插入失败"
        assert exc.error_code == "DATABASE_ERROR"
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc.details["operation"] == "insert"
    
    def test_validation_error(self):
        exc = ValidationError("fund_code", "无效的基金代码")
        
        assert exc.message == "无效的基金代码"
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.status_code == status.HTTP_400_BAD_REQUEST
        assert exc.details["field"] == "fund_code"
    
    def test_update_error(self):
        exc = UpdateError("funds", "更新基金失败")
        
        assert exc.message == "更新基金失败"
        assert exc.error_code == "UPDATE_ERROR"
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc.details["update_type"] == "funds"
