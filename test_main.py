import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app

PAYLOAD = {
    "description": "Lunch",
    "amount": 12.5,
    "category": "food",
    "spent_on": "2026-10-29",
}


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False)
    Base.metadata.create_all(engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_create_and_list(client):
    response = client.post("/api/expenses", json=PAYLOAD)
    assert response.status_code == 201
    assert response.json()["id"] == 1

    listed = client.get("/api/expenses").json()
    assert len(listed) == 1
    assert listed[0]["description"] == "Lunch"


def test_rejects_non_positive_amount(client):
    response = client.post("/api/expenses", json={**PAYLOAD, "amount": -5})
    assert response.status_code == 422


def test_update(client):
    created = client.post("/api/expenses", json=PAYLOAD).json()
    response = client.put(
        f"/api/expenses/{created['id']}", json={**PAYLOAD, "amount": 20}
    )
    assert response.status_code == 200
    assert response.json()["amount"] == 20


def test_delete(client):
    created = client.post("/api/expenses", json=PAYLOAD).json()
    assert client.delete(f"/api/expenses/{created['id']}").status_code == 204
    assert client.get(f"/api/expenses/{created['id']}").status_code == 404


def test_get_missing_returns_404(client):
    assert client.get("/api/expenses/999").status_code == 404