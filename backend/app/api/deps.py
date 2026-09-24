from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user import UserRepository

bearer = HTTPBearer(auto_error=False)
DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> User:
    if not credentials:
        raise AppError(401, "NOT_AUTHENTICATED", "Authentication required")
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = UUID(payload["user_id"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise AppError(401, "INVALID_TOKEN", "Invalid or expired token") from None
    user = await UserRepository(db).get(user_id)
    if not user or not user.is_active:
        raise AppError(401, "INVALID_TOKEN", "Invalid or expired token")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]

