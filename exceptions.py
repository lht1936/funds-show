from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class AppException(Exception):
    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class FundNotFoundError(AppException):
    def __init__(self, fund_code: str):
        super().__init__(
            message=f"基金 {fund_code} 不存在",
            error_code="FUND_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"fund_code": fund_code}
        )


class DataFetchError(AppException):
    def __init__(self, source: str, message: str = "数据获取失败"):
        super().__init__(
            message=message,
            error_code="DATA_FETCH_ERROR",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details={"source": source}
        )


class DatabaseError(AppException):
    def __init__(self, operation: str, message: str = "数据库操作失败"):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"operation": operation}
        )


class ValidationError(AppException):
    def __init__(self, field: str, message: str = "数据验证失败"):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"field": field}
        )


class ConfigurationError(AppException):
    def __init__(self, config_key: str, message: str = "配置错误"):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"config_key": config_key}
        )


class UpdateError(AppException):
    def __init__(self, update_type: str, message: str = "数据更新失败"):
        super().__init__(
            message=message,
            error_code="UPDATE_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"update_type": update_type}
        )
