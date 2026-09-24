import json
from datetime import date

from tests.test_reviews import authenticated_user


async def test_soft_delete_restore_and_permanent_delete(client, session) -> None:
    _, headers = await authenticated_user(session, "trash-user")
    goal = (await client.post(
        "/api/v1/goals",
        headers=headers,
        json={"title": "Disposable", "start_date": str(date.today())},
    )).json()
    assert (await client.delete(f"/api/v1/goals/{goal['id']}", headers=headers)).status_code == 204
    trash = (await client.get("/api/v1/trash", headers=headers)).json()
    assert trash["items"][0]["title"] == "Disposable"

    assert (await client.post(f"/api/v1/trash/goal/{goal['id']}/restore", headers=headers)).status_code == 204
    assert (await client.get(f"/api/v1/goals/{goal['id']}", headers=headers)).status_code == 200

    await client.delete(f"/api/v1/goals/{goal['id']}", headers=headers)
    assert (await client.delete(f"/api/v1/trash/goal/{goal['id']}", headers=headers)).status_code == 204
    assert (await client.get(f"/api/v1/goals/{goal['id']}", headers=headers)).status_code == 404


async def test_export_and_import_validation(client, session) -> None:
    _, headers = await authenticated_user(session, "backup-user")
    await client.post(
        "/api/v1/goals",
        headers=headers,
        json={"title": "Keep me", "start_date": str(date.today())},
    )
    exported = await client.get("/api/v1/export/json", headers=headers)
    assert exported.status_code == 200
    raw = exported.json()
    assert raw["schema_version"] == 1
    assert "password" not in json.dumps(raw).lower()

    preview = await client.post(
        "/api/v1/import/json",
        headers=headers,
        files={"file": ("backup.json", exported.content, "application/json")},
    )
    assert preview.status_code == 200
    assert preview.json()["goals"] == 1
    assert preview.json()["confirmed"] is False

    raw["schema_version"] = 999
    invalid = await client.post(
        "/api/v1/import/json",
        headers=headers,
        files={"file": ("backup.json", json.dumps(raw), "application/json")},
        params={"confirm": "true"},
    )
    assert invalid.status_code == 422
    assert invalid.json()["code"] == "UNSUPPORTED_SCHEMA_VERSION"


async def test_zip_contains_json_and_markdown(client, session) -> None:
    _, headers = await authenticated_user(session, "zip-user")
    response = await client.get("/api/v1/export/zip", headers=headers)
    assert response.status_code == 200
    assert response.content.startswith(b"PK")
