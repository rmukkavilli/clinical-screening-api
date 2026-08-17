from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)

# @pytest.fixture(autouse=True)
# def clear_patients():
#     patients.clear()


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

    response = client.get("/patients?name=Ravi&email=ravi@example.com")

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
