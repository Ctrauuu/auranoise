from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.auth import ChangePasswordRequest, LoginRequest, TokenResponse, UserResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    token = await AuthService(db).login(payload.username, payload.password)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(user)


@router.post("/change-password", status_code=204)
async def change_password(payload: ChangePasswordRequest, db: DbSession, user: CurrentUser) -> None:
    await AuthService(db).change_password(user, payload.current_password, payload.new_password)

