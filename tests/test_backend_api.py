import copy
import sys
from pathlib import Path
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from app import activities, app


@pytest.fixture(autouse=True)
def restore_activities_state():
    original_state = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(copy.deepcopy(original_state))


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_root_redirects_to_static_index(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code in {307, 308}
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_catalog(client):
    # Arrange

    # Act
    response = client.get("/activities")
    payload = response.json()

    # Assert
    assert response.status_code == 200
    assert "Chess Club" in payload
    assert payload["Chess Club"]["max_participants"] == 12
    assert payload["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_for_activity_adds_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"
    expected_message = f"Signed up {email} for {activity_name}"

    # Act
    response = client.post(f"/activities/{quote(activity_name)}/signup?email={email}")
    payload = response.json()

    # Assert
    assert response.status_code == 200
    assert payload["message"] == expected_message
    assert email in activities[activity_name]["participants"]


def test_duplicate_signup_returns_400(client):
    # Arrange
    api_path = "/activities/Chess%20Club/signup?email=michael@mergington.edu"
    expected_detail = "Student already signed up for this activity"

    # Act
    response = client.post(api_path)
    payload = response.json()

    # Assert
    assert response.status_code == 400
    assert payload["detail"] == expected_detail


def test_unregister_participant_removes_email_from_activity(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    expected_message = f"Removed {email} from {activity_name}"

    # Act
    response = client.delete(f"/activities/{quote(activity_name)}/unregister?email={email}")
    payload = response.json()

    # Assert
    assert response.status_code == 200
    assert payload["message"] == expected_message
    assert email not in activities[activity_name]["participants"]
