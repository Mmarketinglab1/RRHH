from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    hash_password,
    password_needs_rehash,
    verify_password,
)
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.models.company import Company
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse

router = APIRouter()


@router.post("/register", response_model=TokenResponse)
@limiter.limit("3/day")
def register(request: Request, payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    company = Company(name=payload.company_name, domain=payload.company_domain)
    user = User(
        company=company,
        email=payload.email.lower(),
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role="admin",
    )
    db.add(company)
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.company_id, user.email)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    users = db.scalars(select(User).where(User.email == payload.email.lower())).all()
    if len(users) > 1:
        raise HTTPException(status_code=400, detail="Email belongs to multiple companies")
    if not users or not verify_password(payload.password, users[0].password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = users[0]
    if password_needs_rehash(user.password_hash):
        user.password_hash = hash_password(payload.password)
        db.commit()

    token = create_access_token(user.id, user.company_id, user.email)
    return TokenResponse(access_token=token)
