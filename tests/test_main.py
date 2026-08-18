import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database import Base, get_db
from app import models

# ---------------------------------------
# Test database setup
# ---------------------------------------

TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


# ---------------------------------------
# Override application's PostgreSQL DB
# with SQLite during tests
# ---------------------------------------

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


client = TestClient(app)


# ---------------------------------------
# Clean database before every test
# ---------------------------------------

@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    yield

    Base.metadata.drop_all(bind=test_engine)


# ---------------------------------------
# Tests
# ---------------------------------------

def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_create_patient_created():
    response1 = client.post(
        "/patients",
        json={
            "full_name": "Test Patient",
            "date_of_birth": "1985-05-20",
            "email": "test@example.com",
        },
    )

    response2 = client.post(
        "/patients",
        json={
            "full_name": "Patient Two",
            "date_of_birth": "1990-06-15",
            "email": "two@example.com",
        },
    )

    assert response1.status_code == 201
    assert response2.status_code == 201

    assert response1.json()["id"] == 1
    assert response2.json()["id"] == 2


def test_get_patients():
    client.post(
        "/patients",
        json={
            "full_name": "Patient One",
            "date_of_birth": "1985-05-20",
            "email": "one@example.com",
        },
    )

    response = client.get("/patients")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["full_name"] == "Patient One"


def test_get_patient_by_name():
    client.post(
        "/patients",
        json={
            "full_name": "Ravi",
            "date_of_birth": "1985-05-20",
            "email": "ravi@example.com",
        },
    )

    response = client.get("/patients/by-name/Ravi")

    assert response.status_code == 200
    assert response.json()["full_name"] == "Ravi"


def test_get_patient_by_id_not_found():
    response = client.get("/patients/999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "999 not found"
    }


def test_get_patient_by_id():
    client.post(
        "/patients",
        json={
            "full_name": "Patient One",
            "date_of_birth": "1985-05-20",
            "email": "one@example.com",
        },
    )

    response = client.get("/patients/1")

    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["full_name"] == "Patient One"


def test_get_patient_by_name_attributes():
    client.post(
        "/patients",
        json={
            "full_name": "Ravi",
            "date_of_birth": "1985-05-20",
            "email": "ravi@example.com",
        },
    )

    response = client.get(
        "/patients?name=Ravi&email=ravi@example.com"
    )

    assert response.status_code == 200
    assert response.json()[0]["full_name"] == "Ravi"


def test_create_patient_invalid_email():
    response = client.post(
        "/patients",
        json={
            "full_name": "Test Patient",
            "date_of_birth": "1985-05-20",
            "email": "not-an-email",
        },
    )

    assert response.status_code == 422

def test_create_patient_missing_name():
    response = client.post(
        "/patients",
        json={
            "date_of_birth": "1985-05-20",
            "email": "test@example.com",
        },
    )

    assert response.status_code == 422

def test_create_patient_duplicate_email():
    patient = {
        "full_name": "Ravi",
        "date_of_birth": "1985-05-20",
        "email": "ravi@example.com",
    }

    response1 = client.post(
        "/patients",
        json=patient,
    )

    response2 = client.post(
        "/patients",
        json=patient,
    )

    assert response1.status_code == 201
    assert response2.status_code == 409

    assert response2.json() == {
        "detail": "Patient with this email already exists"
    }

def test_create_screening():
    patient = {
        "full_name": "Ravi",
        "date_of_birth": "1985-05-20",
        "email": "ravi@example.com",
    }

    patient_response = client.post(
        "/patients",
        json=patient,
    )

    patient_id = patient_response.json()["id"]

    screening_response = client.post(
        "/screenings",
        json={
            "patient_id": patient_id,
        },
    )

    assert screening_response.status_code == 201
    assert screening_response.json() == {
        "patient_id": patient_id,
        "id": 1,
        "status": "scheduled",
    }

def test_create_screening_patient_not_found():
    response = client.post(
        "/screenings",
        json={
            "patient_id": 999,
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Patient not found"
    }

def test_get_screening_by_id():
    patient_response = client.post(
        "/patients",
        json={
            "full_name": "Ravi",
            "date_of_birth": "1985-05-20",
            "email": "ravi@example.com",
        },
    )

    patient_id = patient_response.json()["id"]

    screening_response = client.post(
        "/screenings",
        json={
            "patient_id": patient_id,
        },
    )

    screening_id = screening_response.json()["id"]

    response = client.get(
        f"/screenings/{screening_id}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == screening_id
    assert response.json()["patient_id"] == patient_id
    assert response.json()["status"] == "scheduled"

def test_get_screening_by_id_not_found():
    response = client.get("/screenings/999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "999 not found"
    }

def test_update_screening_status_to_in_progress():
    patient_response = client.post(
        "/patients",
        json={
            "full_name": "Ravi",
            "date_of_birth": "1985-05-20",
            "email": "ravi@example.com",
        },
    )

    patient_id = patient_response.json()["id"]

    screening_response = client.post(
        "/screenings",
        json={
            "patient_id": patient_id,
        },
    )

    screening_id = screening_response.json()["id"]

    response = client.patch(
        f"/screenings/{screening_id}/status",
        json={
            "status": "in_progress",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"
    assert response.json()["id"] == screening_id
    assert response.json()["patient_id"] == patient_id

def test_update_screening_status_invalid_value():
    patient_response = client.post(
        "/patients",
        json={
            "full_name": "Ravi",
            "date_of_birth": "1985-05-20",
            "email": "ravi@example.com",
        },
    )

    patient_id = patient_response.json()["id"]

    screening_response = client.post(
        "/screenings",
        json={
            "patient_id": patient_id,
        },
    )

    screening_id = screening_response.json()["id"]

    response = client.patch(
        f"/screenings/{screening_id}/status",
        json={
            "status": "banana",
        },
    )

    assert response.status_code == 422

def test_update_screening_status_invalid_transition():
    patient_response = client.post(
        "/patients",
        json={
            "full_name": "Ravi",
            "date_of_birth": "1985-05-20",
            "email": "ravi@example.com",
        },
    )

    patient_id = patient_response.json()["id"]

    screening_response = client.post(
        "/screenings",
        json={
            "patient_id": patient_id,
        },
    )

    screening_id = screening_response.json()["id"]

    # scheduled -> in_progress
    response1 = client.patch(
        f"/screenings/{screening_id}/status",
        json={
            "status": "in_progress",
        },
    )

    assert response1.status_code == 200

    # in_progress -> completed
    response2 = client.patch(
        f"/screenings/{screening_id}/status",
        json={
            "status": "completed",
        },
    )

    assert response2.status_code == 200

    # completed -> scheduled should NOT be allowed
    response3 = client.patch(
        f"/screenings/{screening_id}/status",
        json={
            "status": "scheduled",
        },
    )

    assert response3.status_code == 409
    assert response3.json() == {
        "detail": "Cannot change status from completed to scheduled"
    }

def test_update_screening_status_not_found():
    response = client.patch(
        "/screenings/999/status",
        json={
            "status": "in_progress",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "999 not found"
    }

def test_get_screenings_by_patient_id():
    patient1 = client.post(
        "/patients",
        json={
            "full_name": "Patient One",
            "date_of_birth": "1985-05-20",
            "email": "one@example.com",
        },
    )

    patient2 = client.post(
        "/patients",
        json={
            "full_name": "Patient Two",
            "date_of_birth": "1990-06-15",
            "email": "two@example.com",
        },
    )

    patient1_id = patient1.json()["id"]
    patient2_id = patient2.json()["id"]

    client.post(
        "/screenings",
        json={"patient_id": patient1_id},
    )

    client.post(
        "/screenings",
        json={"patient_id": patient2_id},
    )

    response = client.get(
        f"/screenings?patient_id={patient1_id}"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["patient_id"] == patient1_id

def test_get_screenings_by_status():
    patient_response = client.post(
        "/patients",
        json={
            "full_name": "Ravi",
            "date_of_birth": "1985-05-20",
            "email": "ravi@example.com",
        },
    )

    patient_id = patient_response.json()["id"]

    screening1 = client.post(
        "/screenings",
        json={"patient_id": patient_id},
    )

    screening2 = client.post(
        "/screenings",
        json={"patient_id": patient_id},
    )

    screening1_id = screening1.json()["id"]

    client.patch(
        f"/screenings/{screening1_id}/status",
        json={"status": "in_progress"},
    )

    response = client.get(
        "/screenings?status_filter=in_progress"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["status"] == "in_progress"

def test_get_all_screenings():
    patient_response = client.post(
        "/patients",
        json={
            "full_name": "Ravi",
            "date_of_birth": "1985-05-20",
            "email": "ravi@example.com",
        },
    )

    patient_id = patient_response.json()["id"]

    client.post(
        "/screenings",
        json={"patient_id": patient_id},
    )

    client.post(
        "/screenings",
        json={"patient_id": patient_id},
    )

    response = client.get("/screenings")

    assert response.status_code == 200
    assert len(response.json()) == 2