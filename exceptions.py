from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class FundShowException(Exception):
    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class DataFetchError(FundShowException):
    def __init__(
        self,
        message: str = "数据获取失败",
        source: str = "unknown",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="DATA_FETCH_ERROR",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={**(details or {}), "source": source}
        )


class DatabaseError(FundShowException):
    def __init__(
        self,
        message: str = "数据库操作失败",
        operation: str = "unknown",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={**(details or {}), "operation": operation}
        )


class FundNotFoundError(FundShowException):
    def __init__(
        self,
        fund_code: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"基金代码 {fund_code} 不存在",
            error_code="FUND_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={**(details or {}), "fund_code": fund_code}
        )


class InvalidParameterError(FundShowException):
    def __init__(
        self,
        param_name: str,
        reason: str = "参数无效",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"参数 {param_name} 无效: {reason}",
            error_code="INVALID_PARAMETER",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={**(details or {}), "param_name": param_name, "reason": reason}
        )


class ConfigurationError(FundShowException):
    def __init__(
        self,
        config_key: str,
        message: str = "配置错误",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"{message}: {config_key}",
            error_code="CONFIGURATION_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={**(details or {}), "config_key": config_key}
        )


class NetworkError(DataFetchError):
    def __init__(
        self,
        url: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"网络请求失败: {url}",
            source="network",
            details={**(details or {}), "url": url}
        )


def create_error_response(exc: FundShowException) -> Dict[str, Any]:
    return {
        "error": {
            "code": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    }
