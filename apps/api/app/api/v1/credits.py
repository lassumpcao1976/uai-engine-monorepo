from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.credit import CreditBalanceResponse

router = APIRouter()


@router.get("/balance", response_model=CreditBalanceResponse)
def get_credit_balance(current_user: User = Depends(get_current_user)):
    return {"credits": current_user.credits}
