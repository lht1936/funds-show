import pytest
from repo.exceptions import (
    FundShowException,
    DataFetchError,
    DatabaseError,
    FundNotFoundError,
    InvalidParameterError,
    ConfigurationError,
    create_error_response
)


class TestExceptions:
    def test_fund_show_exception_base(self):
        exc = FundShowException(
            message="测试错误",
            error_code="TEST_ERROR",
            status_code=400,
            details={"key": "value"}
        )
        assert exc.message == "测试错误"
        assert exc.error_code == "TEST_ERROR"
        assert exc.status_code == 400
        assert exc.details == {"key": "value"}
        assert str(exc) == "测试错误"

    def test_data_fetch_error(self):
        exc = DataFetchError(
            message="获取数据失败",
            source="akshare",
            details={"url": "http://test.com"}
        )
        assert exc.error_code == "DATA_FETCH_ERROR"
        assert exc.status_code == 503
        assert exc.details["source"] == "akshare"
        assert exc.details["url"] == "http://test.com"

    def test_database_error(self):
        exc = DatabaseError(operation="insert")
        assert exc.error_code == "DATABASE_ERROR"
        assert exc.status_code == 500
        assert exc.details["operation"] == "insert"

    def test_fund_not_found_error(self):
        exc = FundNotFoundError(fund_code="000001")
        assert exc.error_code == "FUND_NOT_FOUND"
        assert exc.status_code == 404
        assert exc.details["fund_code"] == "000001"
        assert "000001" in exc.message

    def test_invalid_parameter_error(self):
        exc = InvalidParameterError(
            param_name="limit",
            reason="必须大于0"
        )
        assert exc.error_code == "INVALID_PARAMETER"
        assert exc.status_code == 400
        assert exc.details["param_name"] == "limit"
        assert exc.details["reason"] == "必须大于0"

    def test_configuration_error(self):
        exc = ConfigurationError(config_key="DATABASE_URL")
        assert exc.error_code == "CONFIGURATION_ERROR"
        assert exc.status_code == 500
        assert exc.details["config_key"] == "DATABASE_URL"

    def test_create_error_response(self):
        exc = FundNotFoundError(fund_code="000001")
        response = create_error_response(exc)

        assert "error" in response
        assert response["error"]["code"] == "FUND_NOT_FOUND"
        assert response["error"]["message"] == "基金代码 000001 不存在"
        assert "details" in response["error"]
