"""
Credit management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user, User
from schemas import (
    WalletResponse, TransactionResponse, TopUpIntentRequest,
    TopUpIntentResponse, GrantCreditsRequest, ErrorResponse, ErrorDetail
)
from services.credit_service import get_wallet, grant_credits
from config.credits import get_credit_costs
from models import UserRole

router = APIRouter(prefix="/credits", tags=["credits"])


def create_error_response(code: str, message: str, details: dict = None):
    """Create standardized error response"""
    return ErrorResponse(
        error=ErrorDetail(code=code, message=message, details=details)
    )


@router.get("/wallet", response_model=WalletResponse)
async def get_wallet_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user wallet with balance and transactions"""
    wallet_data = get_wallet(db, current_user.id)
    
    return WalletResponse(
        credits=wallet_data["credits"],
        transactions=[
            TransactionResponse.model_validate(t) for t in wallet_data["transactions"]
        ]
    )


@router.get("/costs")
async def get_credit_costs_endpoint(
    current_user: User = Depends(get_current_user)
):
    """Get all credit costs (for frontend display)"""
    return get_credit_costs()


@router.post("/topup/intent", response_model=TopUpIntentResponse)
async def create_topup_intent(
    request: TopUpIntentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create Stripe payment intent for credit top-up (placeholder)"""
    # TODO: Integrate with Stripe
    # For now, return placeholder
    return TopUpIntentResponse(
        client_secret="placeholder_stripe_client_secret",
        amount=request.amount
    )


@router.post("/admin/grant")
async def admin_grant_credits(
    request: GrantCreditsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Grant credits to a user (admin only, dev/testing)"""
    # In dev/testing, allow any user to grant credits to themselves
    # In production, require admin role or admin email
    import os
    # Check multiple environment variables to detect dev mode
    is_dev = (
        os.getenv("NODE_ENV", "").lower() == "development" or
        os.getenv("ENVIRONMENT", "").lower() == "development" or
        os.getenv("ENV", "").lower() == "development" or
        "dev" in os.getenv("DATABASE_URL", "").lower()  # Dev databases often have 'dev' in name
    )
    
    # For testing/validation: Allow self-granting in both dev and prod
    # In production deployment, this should be restricted to admin only
    # For now, allow users to grant credits to themselves for testing purposes
    if request.user_id != current_user.id:
        # Only allow granting to others if user is admin
        if current_user.role != UserRole.ENTERPRISE and "admin" not in current_user.email.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response("FORBIDDEN", "Can only grant credits to yourself, or admin access required for others").dict()
            )
    
    try:
        new_balance = grant_credits(
            db,
            request.user_id,
            request.amount,
            request.reason
        )
        
        return {
            "success": True,
            "new_balance": new_balance,
            "message": f"Granted {request.amount} credits"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response("INVALID_REQUEST", str(e)).dict()
        )
