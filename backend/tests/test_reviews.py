from datetime import timedelta

from app.core.security import create_access_token, hash_password
from app.repositories.user import UserRepository
from app.services.review import ReviewService


async def authenticated_user(session, username: str = "reviewer"):
    user = await UserRepository(session).create(username, hash_password("strong-password"))
    await session.commit()
    return user, {"Authorization": f"Bearer {create_access_token(user.id, user.username)}"}


async def test_create_update_duplicate_and_future_review(client, session) -> None:
    user, headers = await authenticated_user(session)
    today = await ReviewService(session, user.id).today()

    response = await client.post("/api/v1/reviews", headers=headers, json={"review_date": str(today)})
    assert response.status_code == 201
    review = response.json()
    assert [section["title"] for section in review["sections"]] == [
        "What I Accomplished Today",
        "Current Goals",
        "Personal Reflections",
        "Problems I Encountered",
    ]

    duplicate = await client.post("/api/v1/reviews", headers=headers, json={"review_date": str(today)})
    assert duplicate.status_code == 409

    future = await client.post(
        "/api/v1/reviews", headers=headers, json={"review_date": str(today + timedelta(days=1))}
    )
    assert future.status_code == 422

    section = review["sections"][0]
    saved = await client.patch(
        f"/api/v1/review-sections/{section['id']}",
        headers=headers,
        json={"content_markdown": "**Done.**"},
    )
    assert saved.status_code == 200
    assert saved.json()["content_markdown"] == "**Done.**"


async def test_review_ownership_is_enforced(client, session) -> None:
    owner, owner_headers = await authenticated_user(session, "owner")
    today = await ReviewService(session, owner.id).today()
    created = await client.post("/api/v1/reviews", headers=owner_headers, json={"review_date": str(today)})
    review_id = created.json()["id"]

    _, other_headers = await authenticated_user(session, "other")
    response = await client.get(f"/api/v1/reviews/{review_id}", headers=other_headers)
    assert response.status_code == 404


async def test_custom_section_can_be_saved_as_preset(client, session) -> None:
    user, headers = await authenticated_user(session)
    today = await ReviewService(session, user.id).today()
    review = (await client.post("/api/v1/reviews", headers=headers, json={"review_date": str(today)})).json()
    response = await client.post(
        f"/api/v1/reviews/{review['id']}/sections",
        headers=headers,
        json={"title": "Learning", "save_to_library": True},
    )
    assert response.status_code == 201
    assert response.json()["preset_id"]
    presets = await client.get("/api/v1/section-presets", headers=headers)
    assert [item["title"] for item in presets.json()] == ["Learning"]


async def test_complete_creates_versioned_immutable_snapshots(client, session) -> None:
    user, headers = await authenticated_user(session)
    today = await ReviewService(session, user.id).today()
    review = (await client.post("/api/v1/reviews", headers=headers, json={"review_date": str(today)})).json()

    first = await client.post(f"/api/v1/reviews/{review['id']}/complete", headers=headers)
    second = await client.post(f"/api/v1/reviews/{review['id']}/complete", headers=headers)
    assert first.json()["status"] == "completed"
    assert second.status_code == 200

    snapshots = await client.get(f"/api/v1/reviews/{review['id']}/snapshots", headers=headers)
    assert [snapshot["version"] for snapshot in snapshots.json()] == [2, 1]
    assert snapshots.json()[0]["snapshot"]["review_date"] == str(today)
