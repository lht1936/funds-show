from sqlalchemy import Column, String, Float, DateTime, Integer, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from repo.database import Base


class Fund(Base):
    __tablename__ = "funds"
    
    fund_code = Column(String(20), primary_key=True, index=True)
    fund_name = Column(String(200), nullable=False)
    fund_type = Column(String(50))
    fund_manager = Column(String(100))
    fund_company = Column(String(200))
    establish_date = Column(Date)
    unit_nav = Column(Float)
    accumulated_nav = Column(Float)
    nav_date = Column(Date)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    holdings = relationship("FundHolding", back_populates="fund", cascade="all, delete-orphan")


class FundHolding(Base):
    __tablename__ = "fund_holdings"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    fund_code = Column(String(20), ForeignKey("funds.fund_code"), nullable=False)
    stock_code = Column(String(20))
    stock_name = Column(String(200))
    holding_ratio = Column(Float)
    holding_shares = Column(Float)
    holding_value = Column(Float)
    report_date = Column(Date)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    fund = relationship("Fund", back_populates="holdings")
