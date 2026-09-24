from datetime import date

from tests.test_reviews import authenticated_user


async def test_goal_task_status_events_and_review_link(client, session) -> None:
    user, headers = await authenticated_user(session, "goal-user")
    goal_response = await client.post(
        "/api/v1/goals",
        headers=headers,
        json={"title": "Learn", "description": "Keep learning", "start_date": str(date.today()), "status": "active"},
    )
    assert goal_response.status_code == 201
    goal = goal_response.json()

    changed = await client.patch(f"/api/v1/goals/{goal['id']}", headers=headers, json={"status": "paused"})
    assert changed.json()["status"] == "paused"

    task_response = await client.post(
        f"/api/v1/goals/{goal['id']}/tasks", headers=headers, json={"title": "Read one chapter"}
    )
    task = task_response.json()
    completed = await client.patch(
        f"/api/v1/goal-tasks/{task['id']}", headers=headers, json={"status": "completed"}
    )
    assert completed.json()["status"] == "completed"

    review = (await client.post(
        "/api/v1/reviews", headers=headers, json={"review_date": str(date.today())}
    )).json()
    links = await client.put(
        f"/api/v1/reviews/{review['id']}/goals", headers=headers, json={"goal_ids": [goal["id"]]}
    )
    assert links.json()["goal_ids"] == [goal["id"]]

    events = await client.get(f"/api/v1/goals/{goal['id']}/events", headers=headers)
    types = [event["event_type"] for event in events.json()]
    assert {"goal_created", "goal_paused", "task_created", "task_completed", "review_linked"} <= set(types)

    snapshot = await client.post(f"/api/v1/reviews/{review['id']}/complete", headers=headers)
    assert snapshot.status_code == 200
    snapshots = (await client.get(f"/api/v1/reviews/{review['id']}/snapshots", headers=headers)).json()
    assert snapshots[0]["snapshot"]["linked_goals"][0]["title"] == "Learn"

