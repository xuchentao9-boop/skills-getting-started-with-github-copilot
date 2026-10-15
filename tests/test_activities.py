from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    original_activities = deepcopy(activities)

    with TestClient(app) as test_client:
        yield test_client

    activities.clear()
    activities.update(original_activities)


def test_root_redirects_to_static_app(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_details(client):
    response = client.get("/activities")

    assert response.status_code == 200
    response_activities = response.json()
    assert "Chess Club" in response_activities

    for activity in response_activities.values():
        assert {"description", "schedule", "max_participants", "participants"} <= activity.keys()


def test_signup_adds_participant(client):
    email = "new-student@mergington.edu"

    response = client.post("/activities/Chess Club/signup", params={"email": email})

    assert response.status_code == 200
    assert email in client.get("/activities").json()["Chess Club"]["participants"]


def test_signup_rejects_duplicate_participant(client):
    email = "new-student@mergington.edu"
    signup_url = "/activities/Chess Club/signup"

    assert client.post(signup_url, params={"email": email}).status_code == 200
    participants_before_duplicate = client.get("/activities").json()["Chess Club"]["participants"]

    response = client.post(signup_url, params={"email": email})

    assert response.status_code == 400
    assert client.get("/activities").json()["Chess Club"]["participants"] == participants_before_duplicate


def test_signup_returns_404_for_unknown_activity(client):
    response = client.post(
        "/activities/Unknown%20Club/signup",
        params={"email": "new-student@mergington.edu"},
    )

    assert response.status_code == 404


def test_unregister_removes_only_requested_participant(client):
    email = "michael@mergington.edu"

    response = client.delete("/activities/Chess Club/signup", params={"email": email})

    assert response.status_code == 200
    participants = client.get("/activities").json()["Chess Club"]["participants"]
    assert email not in participants
    assert "daniel@mergington.edu" in participants


def test_unregister_returns_404_for_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown%20Club/signup",
        params={"email": "new-student@mergington.edu"},
    )

    assert response.status_code == 404


def test_unregister_returns_404_for_nonparticipant(client):
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "not-signed-up@mergington.edu"},
    )

    assert response.status_code == 404