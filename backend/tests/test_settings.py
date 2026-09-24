from tests.test_reviews import authenticated_user


async def test_settings_update_and_validation(client, session) -> None:
    _, headers = await authenticated_user(session, "settings-user")
    response = await client.patch(
        "/api/v1/settings",
        headers=headers,
        json={"timezone": "Asia/Shanghai", "theme": "dark", "trash_retention_days": None},
    )
    assert response.status_code == 200
    assert response.json()["timezone"] == "Asia/Shanghai"
    assert response.json()["theme"] == "dark"
    assert response.json()["trash_retention_days"] is None

    invalid = await client.patch("/api/v1/settings", headers=headers, json={"timezone": "Not/A_Zone"})
    assert invalid.status_code == 422
    assert invalid.json()["code"] == "VALIDATION_ERROR"


async def test_ai_placeholder(client, session) -> None:
    _, headers = await authenticated_user(session, "ai-user")
    response = await client.post("/api/v1/ai/weekly-summary", headers=headers)
    assert response.status_code == 501
    assert response.json()["code"] == "AI_NOT_ENABLED"
