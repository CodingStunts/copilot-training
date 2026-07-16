from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app

client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_activities_state():
    snapshot = deepcopy(activities)
    yield
    activities.clear()
    activities.update(snapshot)


def _activity_path(activity_name: str) -> str:
    return quote(activity_name, safe="")


def _email_path(email: str) -> str:
    return quote(email, safe="")


def test_get_activities_returns_expected_structure():
    response = client.get("/activities")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data

    chess_club = data["Chess Club"]
    assert set(chess_club.keys()) == {
        "description",
        "schedule",
        "max_participants",
        "participants",
    }
    assert isinstance(chess_club["participants"], list)


def test_signup_successfully_adds_participant():
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"

    response = client.post(
        f"/activities/{_activity_path(activity_name)}/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]


def test_signup_duplicate_participant_returns_400_without_duplication():
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    before_count = activities[activity_name]["participants"].count(email)

    response = client.post(
        f"/activities/{_activity_path(activity_name)}/signup",
        params={"email": email},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}
    after_count = activities[activity_name]["participants"].count(email)
    assert before_count == after_count == 1


def test_signup_unknown_activity_returns_404():
    response = client.post(
        f"/activities/{_activity_path('Unknown Club')}/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_successfully_removes_participant():
    activity_name = "Chess Club"
    email = "tempstudent@mergington.edu"

    signup_response = client.post(
        f"/activities/{_activity_path(activity_name)}/signup",
        params={"email": email},
    )
    assert signup_response.status_code == 200

    delete_response = client.delete(
        f"/activities/{_activity_path(activity_name)}/participants/{_email_path(email)}"
    )

    assert delete_response.status_code == 200
    assert delete_response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert email not in activities[activity_name]["participants"]


def test_unregister_unknown_activity_returns_404():
    response = client.delete(
        f"/activities/{_activity_path('Unknown Club')}/participants/{_email_path('student@mergington.edu')}"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_non_member_returns_404():
    activity_name = "Chess Club"
    email = "not-enrolled@mergington.edu"

    response = client.delete(
        f"/activities/{_activity_path(activity_name)}/participants/{_email_path(email)}"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Participant not found in this activity"}
