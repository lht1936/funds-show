from typing import Optional, Dict, Any
from fastapi import HTTPException, status


class FundShowException(Exception):
    """基础异常类"""
    def __init__(
        self,
        message: str = "发生错误",
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class DataFetchException(FundShowException):
    """数据获取异常"""
    def __init__(
        self,
        message: str = "数据获取失败",
        source: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="DATA_FETCH_ERROR",
            details={"source": source, **(details or {})}
        )


class DatabaseException(FundShowException):
    """数据库操作异常"""
    def __init__(
        self,
        message: str = "数据库操作失败",
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details={"operation": operation, **(details or {})}
        )


class FundNotFoundException(FundShowException):
    """基金不存在异常"""
    def __init__(self, fund_code: str):
        super().__init__(
            message=f"基金 {fund_code} 不存在",
            error_code="FUND_NOT_FOUND",
            details={"fund_code": fund_code}
        )


class ValidationException(FundShowException):
    """数据验证异常"""
    def __init__(
        self,
        message: str = "数据验证失败",
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details={"field": field, **(details or {})}
        )


class ExternalAPIException(FundShowException):
    """外部API调用异常"""
    def __init__(
        self,
        message: str = "外部API调用失败",
        api_name: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="EXTERNAL_API_ERROR",
            details={
                "api_name": api_name,
                "status_code": status_code,
                **(details or {})
            }
        )


def raise_http_exception(exception: FundShowException) -> None:
    """将自定义异常转换为HTTPException"""
    status_map = {
        "FUND_NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "VALIDATION_ERROR": status.HTTP_400_BAD_REQUEST,
        "DATA_FETCH_ERROR": status.HTTP_503_SERVICE_UNAVAILABLE,
        "DATABASE_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "EXTERNAL_API_ERROR": status.HTTP_503_SERVICE_UNAVAILABLE,
        "INTERNAL_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    
    raise HTTPException(
        status_code=status_map.get(exception.error_code, status.HTTP_500_INTERNAL_SERVER_ERROR),
        detail={
            "error_code": exception.error_code,
            "message": exception.message,
            "details": exception.details
        }
    )
