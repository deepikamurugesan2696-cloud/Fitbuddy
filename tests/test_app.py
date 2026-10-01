from pathlib import Path

from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app
from app.routes import get_ai


class FakeAI:
    def generate_workout(self, user):
        return "Day 1: Full body\nDay 2: Recovery\nDay 3: Cardio\nDay 4: Rest\nDay 5: Strength\nDay 6: Mobility\nDay 7: Recovery"

    def generate_tip(self, user):
        return "Stay hydrated and include balanced meals and adequate sleep."

    def update_workout(self, user, original_plan, feedback):
        return original_plan + f"\nUpdated using: {feedback}"


def setup_module():
    Path("data").mkdir(exist_ok=True)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_ai] = lambda: FakeAI()


def teardown_module():
    app.dependency_overrides.clear()


def test_health():
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_homepage():
    with TestClient(app) as client:
        response = client.get("/")
    assert response.status_code == 200
    assert "Generate your plan" in response.text


def test_api_generation_and_feedback():
    payload = {
        "username": "Test User",
        "user_id": "test001",
        "age": 22,
        "weight": 65,
        "goal": "general wellness",
        "intensity": "medium",
        "experience": "beginner",
        "days_per_week": 4,
    }
    with TestClient(app) as client:
        response = client.post("/api/v1/plans", json=payload)
        assert response.status_code == 201
        assert "Day 1" in response.json()["workout_plan"]

        response = client.post(
            "/api/v1/plans/test001/feedback",
            json={"feedback": "Add more mobility work"},
        )
        assert response.status_code == 200
        assert "Updated using" in response.json()["updated_plan"]

        response = client.get("/api/v1/users/test001")
        assert response.status_code == 200
        assert response.json()["plan"]["updated_plan"] is not None
