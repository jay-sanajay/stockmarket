"""Register / login / JWT."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from config import JWT_ALGORITHM, get_jwt_secret
from models.db_models import User, Watchlist

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ACCESS_TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire},
        get_jwt_secret(),
        algorithm=JWT_ALGORITHM,
    )


def register_user(db: Session, email: str, password: str) -> User:
    email = email.strip().lower()
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    if db.query(User).filter(User.email == email).first():
        raise ValueError("Email already registered")
    user = User(email=email, hashed_password=hash_password(password))
    db.add(user)
    db.flush()
    db.add(
        Watchlist(
            user_id=user.id,
            name="My Watchlist",
            is_default=True,
            sort_order=0,
        )
    )
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User | None:
    email = email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def verify_token(token: str) -> User | None:
    """Verify JWT token and return user."""
    try:
        payload = jwt.decode(
            token,
            get_jwt_secret(),
            algorithms=[JWT_ALGORITHM]
        )
        user_id = int(payload.get("sub"))
        if user_id is None:
            return None
    except jwt.JWTError:
        return None
    
    from database import SessionLocal
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        return user
    finally:
        db.close()


async def get_current_user_ws(token: str) -> User | None:
    """Get current user from WebSocket token."""
    return verify_token(token)
