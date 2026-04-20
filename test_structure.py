#!/usr/bin/env python3
"""验证代码结构是否正确"""

import sys
import os

# 添加项目路径
sys.path.insert(0, '/Users/linhongting/Documents/fund-show')

def test_imports():
    """测试所有模块是否能正确导入"""
    errors = []
    
    # 测试配置模块
    try:
        from repo.config import Settings, get_settings, reload_settings
        print("✓ config 模块导入成功")
    except Exception as e:
        errors.append(f"✗ config 模块导入失败: {e}")
    
    # 测试异常模块
    try:
        from repo.exceptions import (
            FundShowException,
            DataFetchException,
            DatabaseException,
            FundNotFoundException,
            ValidationException,
            ExternalAPIException,
            raise_http_exception,
        )
        print("✓ exceptions 模块导入成功")
    except Exception as e:
        errors.append(f"✗ exceptions 模块导入失败: {e}")
    
    # 测试数据库模块（不依赖 akshare）
    try:
        from repo.database import DatabaseManager, get_db, get_db_manager
        print("✓ database 模块导入成功")
    except Exception as e:
        errors.append(f"✗ database 模块导入失败: {e}")
    
    # 测试模型模块
    try:
        from repo.models import Fund, FundHolding
        print("✓ models 模块导入成功")
    except Exception as e:
        errors.append(f"✗ models 模块导入失败: {e}")
    
    # 测试 schemas 模块
    try:
        from repo.schemas import (
            FundResponse,
            FundListResponse,
            FundDetailResponse,
            FundHoldingResponse,
            MessageResponse,
        )
        print("✓ schemas 模块导入成功")
    except Exception as e:
        errors.append(f"✗ schemas 模块导入失败: {e}")
    
    return errors


def test_config():
    """测试配置功能"""
    errors = []
    
    try:
        from repo.config import Settings
        
        # 测试默认配置
        settings = Settings()
        assert settings.APP_HOST == "0.0.0.0"
        assert settings.APP_PORT == 8000
        assert settings.is_sqlite == True
        print("✓ 配置默认值测试通过")
        
        # 测试属性
        assert hasattr(settings, 'is_sqlite')
        assert hasattr(settings, 'is_production')
        assert hasattr(settings, 'log_level_int')
        print("✓ 配置属性测试通过")
        
    except Exception as e:
        errors.append(f"✗ 配置测试失败: {e}")
    
    return errors


def test_exceptions():
    """测试异常功能"""
    errors = []
    
    try:
        from repo.exceptions import (
            FundShowException,
            FundNotFoundException,
            raise_http_exception,
        )
        from fastapi import HTTPException
        
        # 测试基础异常
        exc = FundShowException("测试错误", "TEST_ERROR")
        assert exc.message == "测试错误"
        assert exc.error_code == "TEST_ERROR"
        print("✓ 基础异常测试通过")
        
        # 测试基金不存在异常
        exc = FundNotFoundException("000001")
        assert exc.error_code == "FUND_NOT_FOUND"
        assert "000001" in exc.message
        print("✓ FundNotFoundException 测试通过")
        
        # 测试 HTTP 异常转换
        try:
            raise_http_exception(FundNotFoundException("000001"))
        except HTTPException as e:
            assert e.status_code == 404
            print("✓ HTTP 异常转换测试通过")
        
    except Exception as e:
        errors.append(f"✗ 异常测试失败: {e}")
    
    return errors


def test_database_structure():
    """测试数据库结构"""
    errors = []
    
    try:
        from repo.database import get_engine_config
        from repo.config import Settings
        
        # 测试 SQLite 配置
        settings = Settings(DATABASE_URL="sqlite:///test.db")
        config = get_engine_config()
        assert "connect_args" in config
        print("✓ 数据库引擎配置测试通过")
        
    except Exception as e:
        errors.append(f"✗ 数据库结构测试失败: {e}")
    
    return errors


def main():
    """主函数"""
    print("=" * 60)
    print("代码结构验证")
    print("=" * 60)
    
    all_errors = []
    
    print("\n1. 测试模块导入...")
    all_errors.extend(test_imports())
    
    print("\n2. 测试配置功能...")
    all_errors.extend(test_config())
    
    print("\n3. 测试异常功能...")
    all_errors.extend(test_exceptions())
    
    print("\n4. 测试数据库结构...")
    all_errors.extend(test_database_structure())
    
    print("\n" + "=" * 60)
    if all_errors:
        print(f"发现 {len(all_errors)} 个错误:")
        for error in all_errors:
            print(f"  {error}")
        return 1
    else:
        print("所有测试通过！✓")
        return 0


if __name__ == "__main__":
    sys.exit(main())
