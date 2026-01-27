"""
Credit management service
"""
from typing import Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import uuid
from models import User, CreditTransaction, Project
from schemas import ErrorResponse, ErrorDetail


class InsufficientCreditsError(Exception):
    """Raised when user doesn't have enough credits"""
    pass


def charge_credits(
    db: Session,
    user_id: str,
    amount: float,
    reason: str,
    project_id: str = None
) -> Tuple[float, str]:
    """
    Charge credits from user account.
    Returns (new_balance, transaction_id).
    Raises InsufficientCreditsError if insufficient credits.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"User {user_id} not found")
    
    # Convert amount to Decimal for database compatibility
    amount_decimal = Decimal(str(amount))
    
    if user.credits < amount_decimal:
        raise InsufficientCreditsError(
            f"Insufficient credits. Required: {amount}, Available: {user.credits}"
        )
    
    # Deduct credits
    user.credits -= amount_decimal
    
    # Create transaction record
    transaction_id = str(uuid.uuid4())
    transaction = CreditTransaction(
        id=transaction_id,
        user_id=user_id,
        amount=-amount,  # Negative for deduction
        description=reason,
        transaction_type="charge",
        project_id=project_id,
        created_at=datetime.utcnow()
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(user)
    
    return (float(user.credits), transaction_id)


def grant_credits(
    db: Session,
    user_id: str,
    amount: float,
    reason: str = "Admin grant"
) -> float:
    """
    Grant credits to user account.
    Returns new balance.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"User {user_id} not found")
    
    # Convert amount to Decimal for database compatibility
    amount_decimal = Decimal(str(amount))
    
    # Add credits
    user.credits += amount_decimal
    
    # Create transaction record
    transaction = CreditTransaction(
        id=str(uuid.uuid4()),
        user_id=user_id,
        amount=amount,
        description=reason,
        transaction_type="grant",
        created_at=datetime.utcnow()
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(user)
    
    return float(user.credits)


def get_wallet(db: Session, user_id: str) -> dict:
    """Get user wallet with balance and recent transactions"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"User {user_id} not found")
    
    transactions = db.query(CreditTransaction).filter(
        CreditTransaction.user_id == user_id
    ).order_by(CreditTransaction.created_at.desc()).limit(50).all()
    
    return {
        "credits": float(user.credits),
        "transactions": transactions
    }


# Import from centralized config
from config.credits import CREDIT_COSTS, FREE_TIER_STARTING_CREDITS
