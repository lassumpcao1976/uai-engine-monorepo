from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


class CreditTransactionType(str, enum.Enum):
    BUILD = "build"
    EXPORT = "export"
    REFUND = "refund"
    BONUS = "bonus"


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)  # Can be negative for charges
    transaction_type = Column(SQLEnum(CreditTransactionType), nullable=False)
    description = Column(String, nullable=True)
    build_id = Column(Integer, ForeignKey("builds.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="credit_transactions")
