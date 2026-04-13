"""
Tests for the High School Management System API using AAA (Arrange-Act-Assert) pattern.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Arrange: Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def fresh_activities():
    """Arrange: Provide fresh activity data for each test."""
    return {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": []
        }
    }


@pytest.fixture(autouse=True)
def reset_activities(fresh_activities):
    """Arrange: Reset activities to fresh state before each test."""
    activities.clear()
    activities.update(fresh_activities)
    yield
    # Cleanup after test
    activities.clear()


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client, fresh_activities):
        """
        Arrange: Set up test client
        Act: Call GET /activities
        Assert: Verify response contains all activities
        """
        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert "Chess Club" in data
        assert "Programming Class" in data

    def test_get_activities_includes_participant_info(self, client):
        """
        Arrange: Activities loaded with participants
        Act: Call GET /activities
        Assert: Verify activity structure includes participants
        """
        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        chess_club = data["Chess Club"]
        assert "participants" in chess_club
        assert "max_participants" in chess_club
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert isinstance(chess_club["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_new_participant_success(self, client):
        """
        Arrange: Activity exists, participant not registered
        Act: POST signup with valid activity and email
        Assert: Verify 200 status and participant added
        """
        # Arrange
        email = "newstudent@mergington.edu"
        activity = "Programming Class"

        # Act
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity}"
        assert email in activities[activity]["participants"]

    def test_signup_duplicate_participant_fails(self, client):
        """
        Arrange: Participant already registered
        Act: POST signup with same email twice
        Assert: Verify 400 error on duplicate
        """
        # Arrange
        email = "newstudent@mergington.edu"
        activity = "Programming Class"
        
        # Act - First signup
        response1 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response1.status_code == 200

        # Act - Duplicate signup
        response2 = client.post(f"/activities/{activity}/signup?email={email}")

        # Assert
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]

    def test_signup_nonexistent_activity_fails(self, client):
        """
        Arrange: Activity does not exist
        Act: POST signup to non-existent activity
        Assert: Verify 404 error
        """
        # Arrange
        email = "student@mergington.edu"
        activity = "Nonexistent Activity"

        # Act
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_existing_participant_fails(self, client):
        """
        Arrange: Participant already in the activity's participant list
        Act: POST signup with existing participant email
        Assert: Verify 400 error
        """
        # Arrange
        email = "michael@mergington.edu"  # Already in Chess Club
        activity = "Chess Club"

        # Act
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint."""

    def test_unregister_existing_participant_success(self, client):
        """
        Arrange: Participant is registered in activity
        Act: DELETE unregister with valid activity and email
        Assert: Verify 200 status and participant removed
        """
        # Arrange
        email = "michael@mergington.edu"
        activity = "Chess Club"
        assert email in activities[activity]["participants"]

        # Act
        response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Unregistered {email} from {activity}"
        assert email not in activities[activity]["participants"]

    def test_unregister_nonexistent_activity_fails(self, client):
        """
        Arrange: Activity does not exist
        Act: DELETE unregister from non-existent activity
        Assert: Verify 404 error
        """
        # Arrange
        email = "student@mergington.edu"
        activity = "Nonexistent Activity"

        # Act
        response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_not_registered_participant_fails(self, client):
        """
        Arrange: Participant is not registered in activity
        Act: DELETE unregister with email not in participants
        Assert: Verify 400 error
        """
        # Arrange
        email = "notregistered@mergington.edu"
        activity = "Programming Class"
        assert email not in activities[activity]["participants"]

        # Act
        response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )

        # Assert
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_unregister_then_signup_again_succeeds(self, client):
        """
        Arrange: Participant is registered
        Act: Unregister, then signup again
        Assert: Verify both operations succeed
        """
        # Arrange
        email = "michael@mergington.edu"
        activity = "Chess Club"

        # Act - Unregister
        response1 = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert response1.status_code == 200

        # Act - Signup again
        response2 = client.post(
            f"/activities/{activity}/signup?email={email}"
        )

        # Assert
        assert response2.status_code == 200
        assert email in activities[activity]["participants"]
