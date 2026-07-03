"""Authentication middleware"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWTError
from enum import Enum
from typing import Optional
from app.config import settings


class UserRole(str, Enum):
    """User roles"""

    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"


security = HTTPBearer()


class CurrentUser:
    """Current authenticated user"""

    def __init__(self, user_id: str, email: str, role: UserRole):
        self.user_id = user_id
        self.email = email
        self.role = role


async def verify_token(token: str) -> dict:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        return payload
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:
    """Get current authenticated user from token"""
    token = credentials.credentials
    payload = await verify_token(token)

    user_id = payload.get("sub")
    email = payload.get("email")
    role = payload.get("role")

    if not user_id or not email or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return CurrentUser(user_id=user_id, email=email, role=UserRole(role))


async def require_role(required_roles: list[UserRole]):
    """Dependency to check if user has required role"""

    async def role_checker(current_user: CurrentUser = Depends(get_current_user)):
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_checker