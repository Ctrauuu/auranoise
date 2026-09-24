from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.repositories.user import UserRepository
from app.services.auth import bootstrap_initial_user


async def test_initial_user_creation(session) -> None:
    user = await bootstrap_initial_user(session)
    assert user and user.username == settings.initial_username
    assert user.password_hash != settings.initial_password
    assert verify_password(settings.initial_password, user.password_hash)
    assert await bootstrap_initial_user(session) is None


async def test_login_me_and_change_password(client, session) -> None:
    user = await UserRepository(session).create("alice", hash_password("old-password"))
    await session.commit()

    response = await client.post("/api/v1/auth/login", json={"username": "alice", "password": "old-password"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.json() == {"id": str(user.id), "username": "alice"}

    response = await client.post(
        "/api/v1/auth/change-password",
        headers=headers,
        json={"current_password": "old-password", "new_password": "new-password"},
    )
    assert response.status_code == 204
    response = await client.post("/api/v1/auth/login", json={"username": "alice", "password": "new-password"})
    assert response.status_code == 200


async def test_bad_login_uses_error_schema(client) -> None:
    response = await client.post("/api/v1/auth/login", json={"username": "missing", "password": "nope"})
    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_CREDENTIALS"

