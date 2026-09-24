from datetime import timedelta

from sqlalchemy import select

from app.models.user import UserSettings
from app.services.review import ReviewService
from tests.test_reviews import authenticated_user


async def test_search_timeline_and_stats_streak(client, session) -> None:
    user, headers = await authenticated_user(session, "discoverer")
    today = await ReviewService(session, user.id).today()
    review_ids = []
    for offset in (0, 1, 2):
        created = await client.post(
            "/api/v1/reviews", headers=headers, json={"review_date": str(today - timedelta(days=offset))}
        )
        review = created.json()
        review_ids.append(review["id"])
        await client.patch(
            f"/api/v1/review-sections/{review['sections'][0]['id']}",
            headers=headers,
            json={"content_markdown": "A uniquely searchable reflection"},
        )
        await client.post(f"/api/v1/reviews/{review['id']}/complete", headers=headers)

    search = await client.get("/api/v1/search", headers=headers, params={"keyword": "uniquely searchable"})
    assert search.status_code == 200
    assert search.json()["total"] >= 3
    assert {item["type"] for item in search.json()["items"]} >= {"review", "section"}

    timeline = await client.get("/api/v1/timeline", headers=headers)
    assert timeline.status_code == 200
    assert any(item["type"] == "review_completed" for item in timeline.json()["items"])

    stats = (await client.get("/api/v1/stats/summary", headers=headers)).json()
    assert stats["current_review_streak"] == 3
    assert stats["longest_review_streak"] == 3


async def test_timezone_drives_today(client, session) -> None:
    user, headers = await authenticated_user(session, "timezone-user")
    settings = await session.scalar(select(UserSettings).where(UserSettings.user_id == user.id))
    settings.timezone = "Pacific/Kiritimati"
    await session.commit()
    expected = await ReviewService(session, user.id).today()
    created = await client.post("/api/v1/reviews", headers=headers, json={"review_date": str(expected)})
    assert created.status_code == 201
    today = await client.get("/api/v1/reviews/today", headers=headers)
    assert today.json()["review_date"] == str(expected)
