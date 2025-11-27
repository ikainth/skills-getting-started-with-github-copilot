"""
FastAPI tests for the High School Activities Management System
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original state
    original = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
    }
    yield
    # Reset after test
    activities.clear()
    activities.update(original)


class TestActivitiesEndpoint:
    """Test the /activities endpoint"""

    def test_get_activities(self, client, reset_activities):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert data["Chess Club"]["description"] == "Learn strategies and compete in chess tournaments"

    def test_activities_have_correct_structure(self, client, reset_activities):
        """Test that activities have the required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)


class TestSignupEndpoint:
    """Test the signup endpoint"""

    def test_signup_for_activity(self, client, reset_activities):
        """Test signing up for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up test@mergington.edu for Chess Club" in data["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        assert "test@mergington.edu" in activities_response.json()["Chess Club"]["participants"]

    def test_signup_duplicate_email(self, client, reset_activities):
        """Test that duplicate signups are rejected"""
        # First signup
        response1 = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response1.status_code == 400
        assert "already signed up" in response1.json()["detail"]

    def test_signup_nonexistent_activity(self, client, reset_activities):
        """Test signing up for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_special_characters_in_email(self, client, reset_activities):
        """Test signup with special characters in email"""
        response = client.post(
            "/activities/Chess Club/signup?email=test+tag@mergington.edu"
        )
        assert response.status_code == 200


class TestUnregisterEndpoint:
    """Test the unregister endpoint"""

    def test_unregister_participant(self, client, reset_activities):
        """Test unregistering a participant"""
        # Unregister an existing participant
        response = client.delete(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered michael@mergington.edu" in data["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        assert "michael@mergington.edu" not in activities_response.json()["Chess Club"]["participants"]

    def test_unregister_nonexistent_participant(self, client, reset_activities):
        """Test unregistering a participant that doesn't exist"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=nonexistent@mergington.edu"
        )
        assert response.status_code == 400
        assert "Participant not found" in response.json()["detail"]

    def test_unregister_from_nonexistent_activity(self, client, reset_activities):
        """Test unregistering from an activity that doesn't exist"""
        response = client.delete(
            "/activities/Nonexistent Club/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_and_unregister_flow(self, client, reset_activities):
        """Test the complete flow of signing up and then unregistering"""
        email = "newcomer@mergington.edu"
        
        # Sign up
        signup_response = client.post(
            f"/activities/Programming Class/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Verify signup
        activities_response = client.get("/activities")
        assert email in activities_response.json()["Programming Class"]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/Programming Class/unregister?email={email}"
        )
        assert unregister_response.status_code == 200
        
        # Verify unregister
        activities_response = client.get("/activities")
        assert email not in activities_response.json()["Programming Class"]["participants"]


class TestRootEndpoint:
    """Test the root endpoint"""

    def test_root_redirects(self, client):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
