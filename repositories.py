from typing import List, Optional, Type, TypeVar, Generic, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import logging

from repo.config import get_settings
from repo.models import Fund, FundHolding
from repo.exceptions import DatabaseError

settings = get_settings()

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    def __init__(self, db: Session, model: Type[ModelType]):
        self.db = db
        self.model = model

    def _commit(self) -> None:
        try:
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"数据库提交失败: {str(e)}")
            raise DatabaseError(
                operation="commit",
                message="数据库事务提交失败",
                details={"error": str(e)}
            )

    def get_by_id(self, id: Any) -> Optional[ModelType]:
        try:
            return self.db.query(self.model).get(id)
        except SQLAlchemyError as e:
            logger.error(f"查询失败: {str(e)}")
            raise DatabaseError(
                operation="get_by_id",
                message=f"查询 {self.model.__name__} 失败",
                details={"error": str(e)}
            )

    def create(self, obj_in: Dict[str, Any]) -> ModelType:
        try:
            db_obj = self.model(**obj_in)
            self.db.add(db_obj)
            self._commit()
            self.db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            logger.error(f"创建失败: {str(e)}")
            raise DatabaseError(
                operation="create",
                message=f"创建 {self.model.__name__} 失败",
                details={"error": str(e)}
            )

    def update(self, db_obj: ModelType, obj_in: Dict[str, Any]) -> ModelType:
        try:
            for key, value in obj_in.items():
                if value is not None and hasattr(db_obj, key):
                    setattr(db_obj, key, value)
            if hasattr(db_obj, 'updated_at'):
                setattr(db_obj, 'updated_at', datetime.utcnow())
            self._commit()
            self.db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            logger.error(f"更新失败: {str(e)}")
            raise DatabaseError(
                operation="update",
                message=f"更新 {self.model.__name__} 失败",
                details={"error": str(e)}
            )

    def delete(self, id: Any) -> bool:
        try:
            obj = self.get_by_id(id)
            if obj:
                self.db.delete(obj)
                self._commit()
                return True
            return False
        except SQLAlchemyError as e:
            logger.error(f"删除失败: {str(e)}")
            raise DatabaseError(
                operation="delete",
                message=f"删除 {self.model.__name__} 失败",
                details={"error": str(e)}
            )

    def list_all(self, skip: int = 0, limit: int = settings.DEFAULT_LIST_LIMIT) -> List[ModelType]:
        try:
            return self.db.query(self.model).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"列表查询失败: {str(e)}")
            raise DatabaseError(
                operation="list_all",
                message=f"查询 {self.model.__name__} 列表失败",
                details={"error": str(e)}
            )

    def count(self) -> int:
        try:
            return self.db.query(self.model).count()
        except SQLAlchemyError as e:
            logger.error(f"计数查询失败: {str(e)}")
            raise DatabaseError(
                operation="count",
                message=f"统计 {self.model.__name__} 数量失败",
                details={"error": str(e)}
            )


class FundRepository(BaseRepository[Fund]):
    def __init__(self, db: Session):
        super().__init__(db, Fund)

    def get_by_code(self, fund_code: str) -> Optional[Fund]:
        try:
            return self.db.query(Fund).filter(Fund.fund_code == fund_code).first()
        except SQLAlchemyError as e:
            logger.error(f"查询基金失败: {str(e)}")
            raise DatabaseError(
                operation="get_by_code",
                message="查询基金信息失败",
                details={"fund_code": fund_code, "error": str(e)}
            )

    def list_funds(
        self,
        skip: int = 0,
        limit: int = settings.DEFAULT_LIST_LIMIT,
        fund_type: Optional[str] = None
    ) -> tuple[int, List[Fund]]:
        try:
            query = self.db.query(Fund)
            if fund_type:
                query = query.filter(Fund.fund_type.ilike(f"%{fund_type}%"))
            total = query.count()
            funds = query.order_by(Fund.updated_at.desc()).offset(skip).limit(limit).all()
            return total, funds
        except SQLAlchemyError as e:
            logger.error(f"查询基金列表失败: {str(e)}")
            raise DatabaseError(
                operation="list_funds",
                message="查询基金列表失败",
                details={"error": str(e)}
            )

    def create_or_update(self, fund_data: Dict[str, Any]) -> tuple[Fund, bool]:
        fund_code = fund_data.get('fund_code')
        existing_fund = self.get_by_code(fund_code)

        if existing_fund:
            fund_data['updated_at'] = datetime.utcnow()
            return self.update(existing_fund, fund_data), False
        else:
            return self.create(fund_data), True

    def get_all_codes(self) -> List[str]:
        try:
            return [f.fund_code for f in self.db.query(Fund).all()]
        except SQLAlchemyError as e:
            logger.error(f"查询基金代码列表失败: {str(e)}")
            raise DatabaseError(
                operation="get_all_codes",
                message="查询基金代码列表失败",
                details={"error": str(e)}
            )


class FundHoldingRepository(BaseRepository[FundHolding]):
    def __init__(self, db: Session):
        super().__init__(db, FundHolding)

    def get_by_fund_code(self, fund_code: str) -> List[FundHolding]:
        try:
            return self.db.query(FundHolding).filter(
                FundHolding.fund_code == fund_code
            ).order_by(FundHolding.holding_ratio.desc().nullslast()).all()
        except SQLAlchemyError as e:
            logger.error(f"查询基金持仓失败: {str(e)}")
            raise DatabaseError(
                operation="get_by_fund_code",
                message="查询基金持仓失败",
                details={"fund_code": fund_code, "error": str(e)}
            )

    def replace_holdings(self, fund_code: str, holdings_data: List[Dict[str, Any]]) -> int:
        try:
            self.db.query(FundHolding).filter(
                FundHolding.fund_code == fund_code
            ).delete()

            count = 0
            for holding_data in holdings_data:
                holding = FundHolding(**holding_data)
                self.db.add(holding)
                count += 1

            self._commit()
            return count
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"替换基金持仓失败: {str(e)}")
            raise DatabaseError(
                operation="replace_holdings",
                message="替换基金持仓失败",
                details={"fund_code": fund_code, "error": str(e)}
            )


class RepositoryFactory:
    def __init__(self, db: Session):
        self.db = db
        self._fund_repo: Optional[FundRepository] = None
        self._fund_holding_repo: Optional[FundHoldingRepository] = None

    @property
    def fund(self) -> FundRepository:
        if self._fund_repo is None:
            self._fund_repo = FundRepository(self.db)
        return self._fund_repo

    @property
    def fund_holding(self) -> FundHoldingRepository:
        if self._fund_holding_repo is None:
            self._fund_holding_repo = FundHoldingRepository(self.db)
        return self._fund_holding_repo
