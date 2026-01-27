"""
Authentication routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import uuid
from datetime import timedelta

from database import get_db
from models import User, UserRole
from auth import get_password_hash, verify_password, create_access_token, get_current_user
from config.credits import FREE_TIER_STARTING_CREDITS
from schemas import (
    SignUpRequest, SignInRequest, AuthResponse, UserResponse,
    ErrorResponse, ErrorDetail
)

router = APIRouter(prefix="/auth", tags=["auth"])


def create_error_response(code: str, message: str, details: dict = None):
    """Create standardized error response"""
    return ErrorResponse(
        error=ErrorDetail(code=code, message=message, details=details)
    )


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignUpRequest, db: Session = Depends(get_db)):
    """Create a new user account"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(
                "USER_EXISTS",
                "User with this email already exists"
            ).dict()
        )
    
    # Create new user
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email=request.email,
        name=request.name,
        password_hash=get_password_hash(request.password),
        role=UserRole.FREE,
        credits=FREE_TIER_STARTING_CREDITS
    )
    
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(
                "USER_EXISTS",
                "User with this email already exists"
            ).dict()
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user.id})
    
    return AuthResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/signin", response_model=AuthResponse)
async def signin(request: SignInRequest, db: Session = Depends(get_db)):
    """Sign in with email and password"""
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=create_error_response(
                "INVALID_CREDENTIALS",
                "Invalid email or password"
            ).dict()
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user.id})
    
    return AuthResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user"""
    return UserResponse.model_validate(current_user)
