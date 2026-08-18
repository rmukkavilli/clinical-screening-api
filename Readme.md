cd C:\Users\ravir\OneDrive\Desktop\pytest-fhir\rmukkavilli\clinical-screening-api

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

.\.venv\Scripts\Activate.ps1

python -m pytest

fastapi dev app\main.py



# Clinical Screening API

A backend portfolio project built with **FastAPI**, **SQLAlchemy**, **PostgreSQL**, **Alembic**, and **PyTest**.

Repository: https://github.com/rmukkavilli/clinical-screening-api

The project models a simplified clinical screening workflow and demonstrates API design, relational data modeling, validation, business rules, database migrations, error handling, filtering, and automated testing.

---

## Project Workflow

```text
Patient
   ↓
Create Screening
   ↓
scheduled
   ↓
in_progress
   ├──→ completed
   └──→ failed
```

The API prevents invalid transitions such as:

```text
completed → scheduled
```

and rejects unsupported status values such as:

```text
banana
```

---

## Current Status

```text
[✓] FastAPI application
[✓] PostgreSQL database
[✓] SQLAlchemy ORM
[✓] Patient model
[✓] Screening model
[✓] Foreign-key relationship
[✓] Pydantic validation
[✓] Patient APIs
[✓] Screening APIs
[✓] Filtering
[✓] Business status transitions
[✓] Error handling
[✓] Alembic migrations
[✓] FastAPI router refactor
[✓] PyTest test infrastructure
[✓] 21 passing tests
[ ] Docker
[ ] GitHub Actions CI
[ ] Final deployment
```

---

## Technology Stack

| Area | Technology |
|---|---|
| Language | Python |
| API Framework | FastAPI |
| ORM | SQLAlchemy |
| Application Database | PostgreSQL |
| Database Migrations | Alembic |
| Validation | Pydantic |
| Automated Testing | PyTest |
| API Testing | FastAPI TestClient |
| Test Database | SQLite in-memory |
| Containerization | Docker — next |
| CI/CD | GitHub Actions — next |

---

## Project Structure

```text
clinical-screening-api/
├── .env
├── .gitignore
├── alembic.ini
├── requirements.txt
│
├── alembic/
│   ├── env.py
│   ├── README
│   ├── script.py.mako
│   └── versions/
│       └── 4e12305ce03d_initial_schema.py
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   │
│   └── routers/
│       ├── __init__.py
│       ├── patients.py
│       └── screenings.py
│
└── tests/
    └── test_main.py
```

---

## Application Responsibilities

### `app/main.py`

Creates the FastAPI application, registers the routers, and exposes the health endpoint.

```python
from fastapi import FastAPI
from app.routers import patients, screenings

app = FastAPI()

app.include_router(patients.router)
app.include_router(screenings.router)


@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

### `app/database.py`

Responsible for:

- loading `DATABASE_URL`
- creating the SQLAlchemy engine
- creating `SessionLocal`
- defining the shared SQLAlchemy `Base`
- exposing `get_db()` for FastAPI dependency injection

### `app/models.py`

Defines the SQLAlchemy database models:

- `Patient`
- `Screening`

### `app/schemas.py`

Defines the Pydantic request and response models:

- `PatientCreate`
- `PatientResponse`
- `ScreeningCreate`
- `ScreeningResponse`
- `ScreeningStatusUpdate`

### `app/routers/patients.py`

Contains all Patient API endpoints.

### `app/routers/screenings.py`

Contains all Screening API endpoints and the screening status transition rules.

---

# Database Model

## Patient

```text
patients
--------------------------------
id              integer PK
full_name       varchar(200)
date_of_birth   date
email           varchar(255) UNIQUE
```

Creating another patient with the same email returns:

```text
409 Conflict
```

## Screening

```text
screenings
--------------------------------
id              integer PK
patient_id      integer FK → patients.id
status          varchar(50)
```

Every screening belongs to an existing patient. A screening cannot be created for a nonexistent patient.

---

# API Endpoints

## Health

### `GET /health`

```json
{
  "status": "healthy"
}
```

---

# Patient API

## Create Patient

### `POST /patients`

Request:

```json
{
  "full_name": "Ravi",
  "date_of_birth": "1985-05-20",
  "email": "ravi@example.com"
}
```

Successful response:

```text
201 Created
```

Example response:

```json
{
  "full_name": "Ravi",
  "date_of_birth": "1985-05-20",
  "email": "ravi@example.com",
  "id": 1
}
```

Duplicate email:

```text
409 Conflict
```

```json
{
  "detail": "Patient with this email already exists"
}
```

## List Patients

### `GET /patients`

Returns all patients.

## Filter Patients

```text
GET /patients?name=Ravi
GET /patients?email=ravi@example.com
GET /patients?name=Ravi&email=ravi@example.com
```

## Get Patient by ID

### `GET /patients/{patient_id}`

Example:

```text
GET /patients/1
```

Missing patient:

```text
404 Not Found
```

## Get Patient by Name

### `GET /patients/by-name/{patient_name}`

Example:

```text
GET /patients/by-name/Ravi
```

---

# Screening API

## Create Screening

### `POST /screenings`

Request:

```json
{
  "patient_id": 1
}
```

A new screening starts with:

```text
scheduled
```

Example response:

```json
{
  "patient_id": 1,
  "id": 1,
  "status": "scheduled"
}
```

If the patient does not exist:

```text
404 Not Found
```

```json
{
  "detail": "Patient not found"
}
```

## List All Screenings

### `GET /screenings`

Returns all screenings.

## Filter Screenings by Patient

```text
GET /screenings?patient_id=1
```

## Filter Screenings by Status

```text
GET /screenings?status_filter=in_progress
```

## Get Screening by ID

### `GET /screenings/{screening_id}`

Example:

```text
GET /screenings/1
```

## Update Screening Status

### `PATCH /screenings/{screening_id}/status`

Request:

```json
{
  "status": "in_progress"
}
```

The endpoint:

1. loads the screening from the database
2. returns `404` if it does not exist
3. reads the current status
4. determines allowed next statuses
5. rejects invalid transitions with `409`
6. updates the status
7. commits the database transaction
8. refreshes and returns the updated record

---

# Screening Status Rules

Supported status values:

```text
scheduled
in_progress
completed
failed
```

Allowed transitions:

```text
scheduled → in_progress

in_progress → completed
in_progress → failed

completed → no further transition
failed    → no further transition
```

Example valid transition:

```text
scheduled → in_progress
```

Example invalid transition:

```text
completed → scheduled
```

returns:

```text
409 Conflict
```

---

## Validation vs Business Logic

Invalid status value:

```json
{
  "status": "banana"
}
```

Result:

```text
422 Unprocessable Entity
```

because Pydantic rejects the value before the endpoint business logic runs.

An invalid transition such as:

```text
completed → scheduled
```

uses valid status values, but violates the workflow rule, so it returns:

```text
409 Conflict
```

---

# SQLAlchemy Examples

Primary-key lookup:

```python
patient = db.get(Patient, patient_id)
```

Conceptually similar to:

```sql
SELECT *
FROM patients
WHERE id = :patient_id;
```

Filtered screening query:

```python
query = select(Screening)

if patient_id is not None:
    query = query.where(
        Screening.patient_id == patient_id
    )

return db.scalars(query).all()
```

Case-insensitive patient lookup:

```python
query = select(Patient).where(
    Patient.full_name.ilike(patient_name)
)
```

---

# PostgreSQL Configuration

The application uses PostgreSQL. The database connection is supplied through an environment variable.

Example `.env`:

```env
DATABASE_URL=postgresql+psycopg://clinical_app:YOUR_PASSWORD@localhost:5432/clinical_screening
```

Do **not** commit the real `.env` file.

Recommended `.gitignore` entries:

```gitignore
.env
.venv/
__pycache__/
*.pyc
.pytest_cache/
```

---

# PyTest Test Architecture

The application uses PostgreSQL, but automated API tests currently use an isolated in-memory SQLite database.

```python
TEST_DATABASE_URL = "sqlite://"
```

The test engine uses:

```python
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
```

## Why SQLite for Tests?

The SQLite test database provides:

- fast execution
- deterministic state
- isolation from developer PostgreSQL data
- no dependency on a running PostgreSQL server for every test run

A future enhancement is a PostgreSQL integration-test environment using Docker.

## Why `StaticPool`?

An in-memory SQLite database normally exists only for the lifetime of its connection. `StaticPool` keeps the same connection available so the TestClient requests in a test see the same in-memory database.

## Why `check_same_thread=False`?

SQLite normally restricts one connection to the thread that created it. FastAPI TestClient can cross thread boundaries, so this option allows the test connection to be reused.

---

# FastAPI Dependency Override

The application normally uses:

```python
get_db
```

for PostgreSQL sessions.

During tests:

```python
app.dependency_overrides[get_db] = override_get_db
```

Conceptually:

```text
Application
get_db
   ↓
PostgreSQL
```

During tests:

```text
get_db
   ↓
dependency override
   ↓
SQLite in-memory
```

---

# Test Database Isolation

The test suite resets the schema for every test:

```python
@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    yield

    Base.metadata.drop_all(bind=test_engine)
```

Benefits:

- each test starts clean
- tests do not depend on execution order
- data from one test cannot affect another
- failures are easier to reproduce

---

# Automated Test Coverage

Current checkpoint:

```text
21 tests passing
```

Coverage includes:

### Health

- health endpoint

### Patients

- create patient
- create multiple patients
- get all patients
- get patient by ID
- patient not found
- get patient by name
- filter by name/email
- invalid email
- missing required name
- duplicate email returns `409`

### Screenings

- create screening
- nonexistent patient returns `404`
- get screening by ID
- screening not found
- valid status update
- invalid status value returns `422`
- invalid status transition returns `409`
- update nonexistent screening
- filter by patient ID
- filter by status
- list all screenings

Run all tests:

```powershell
python -m pytest -v
```

Run one test:

```powershell
python -m pytest tests/test_main.py::test_create_screening -v
```

Stop on the first failure:

```powershell
python -m pytest -v -x
```

---

# Alembic Database Migrations

Alembic manages PostgreSQL schema evolution.

Current initial migration:

```text
alembic/versions/4e12305ce03d_initial_schema.py
```

Check the database revision:

```powershell
alembic current
```

Current expected state:

```text
4e12305ce03d (head)
```

Check whether SQLAlchemy models differ from the PostgreSQL schema:

```powershell
alembic check
```

Expected when synchronized:

```text
No new upgrade operations detected.
```

Create a migration after changing models:

```powershell
alembic revision --autogenerate -m "describe schema change"
```

Review the migration before applying it.

Then:

```powershell
alembic upgrade head
```

Migration flow:

```text
models.py change
      ↓
alembic revision --autogenerate
      ↓
review migration
      ↓
alembic upgrade head
      ↓
PostgreSQL schema updated
```

---

# Local Development Setup

## 1. Clone the Repository

```powershell
git clone https://github.com/rmukkavilli/clinical-screening-api.git
cd clinical-screening-api
```

## 2. Create a Virtual Environment

```powershell
python -m venv .venv
```

## 3. Activate It

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 4. Verify Python

```powershell
(Get-Command python).Source
```

## 5. Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

## 6. Configure `.env`

```env
DATABASE_URL=postgresql+psycopg://clinical_app:YOUR_PASSWORD@localhost:5432/clinical_screening
```

## 7. Apply Migrations

```powershell
alembic upgrade head
```

## 8. Start FastAPI

```powershell
fastapi dev app\main.py
```

Application:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

Health endpoint:

```text
http://127.0.0.1:8000/health
```

---

# HTTP Error Strategy

| Scenario | Status |
|---|---|
| Successful GET | 200 |
| Resource created | 201 |
| Resource not found | 404 |
| Duplicate patient email | 409 |
| Invalid status transition | 409 |
| Invalid request/schema | 422 |

---

# Router Architecture

The application originally placed endpoints directly in `main.py`. As the API grew, routes were moved into FastAPI `APIRouter` modules.

Current design:

```text
main.py
├── FastAPI startup
├── router registration
└── health endpoint

routers/patients.py
└── Patient API

routers/screenings.py
├── Screening API
└── screening status rules
```

Example:

```python
router = APIRouter(
    prefix="/patients",
    tags=["patients"],
)
```

combined with:

```python
@router.get("/{patient_id}")
```

becomes:

```text
GET /patients/{patient_id}
```

---

# Debugging Notes

## `405 Method Not Allowed`

Usually means the path exists but that HTTP method is not registered.

Example:

```text
POST /patients exists
GET /patients missing
```

## `404 Not Found` After Router Refactor

Verify the routers are included:

```python
app.include_router(patients.router)
app.include_router(screenings.router)
```

## `KeyError: 'id'` in Tests

A `KeyError` can be a downstream symptom. If this fails:

```python
screening_response.json()["id"]
```

inspect whether the API actually returned something like:

```json
{
  "detail": "Not Found"
}
```

Check the original HTTP status before debugging the missing key.

## SQLAlchemy `IntegrityError`

Duplicate email handling uses:

```python
try:
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)

except IntegrityError:
    db.rollback()

    raise HTTPException(
        status_code=409,
        detail="Patient with this email already exists",
    )
```

`db.rollback()` is required after a failed database transaction before the SQLAlchemy session can safely continue.

---

# Backend Concepts Demonstrated

- REST API design
- FastAPI routing
- HTTP methods and status codes
- request validation
- response models
- dependency injection
- relational database design
- primary keys
- foreign keys
- uniqueness constraints
- SQLAlchemy ORM
- SQLAlchemy sessions
- filtered queries
- transactions
- commit and rollback
- business-state transitions
- error handling
- environment-based configuration
- database migrations
- PyTest API automation
- dependency overrides
- isolated test databases
- router modularization

---

# Interview Summary

> I built a FastAPI backend for a clinical screening workflow using PostgreSQL and SQLAlchemy. I modeled patients and screenings with a relational foreign-key design, implemented validation and HTTP error handling, added screening lifecycle business rules, introduced Alembic migrations, and built isolated API automation with PyTest using FastAPI dependency overrides and an in-memory SQLite database. As the application grew, I refactored the endpoints into dedicated FastAPI routers while maintaining a fully passing automated regression suite.

---

# Interview Discussion Points

### Why PostgreSQL?

PostgreSQL is the primary relational database for the application and provides a production-relevant relational data model.

### Why SQLAlchemy?

SQLAlchemy lets the application express database operations through Python models and query constructs while executing SQL against PostgreSQL.

### Why Alembic?

SQLAlchemy models describe the desired schema; Alembic provides controlled and versioned database schema evolution.

### Why SQLite for Tests?

SQLite in-memory testing provides fast, isolated API tests without modifying developer PostgreSQL data. A future enhancement is PostgreSQL integration testing through Docker.

### Why FastAPI Routers?

Routers separate application startup from domain-specific endpoints and make the project easier to maintain as it grows.

### Why `409` for Invalid Status Transitions?

The requested status is valid, but the operation conflicts with the current resource state.

### Why `422` for an Unsupported Status?

Pydantic rejects the request because the body does not satisfy the API schema.

---

# Next Steps for Portfolio-Ready V1

```text
1. Dockerize FastAPI + PostgreSQL
2. Add GitHub Actions CI
3. Add .env.example
4. Review requirements.txt
5. Verify setup from a fresh clone
6. Final repository cleanup
7. Update portfolio project card to COMPLETED
```

---

# Possible V2 Enhancements

- authentication
- JWT/token-protected endpoints
- Redis
- background processing
- retry logic
- idempotency
- PostgreSQL integration-test container
- structured logging
- observability
- pagination
- timestamps
- screening audit history
- service layer
- repository/data-access layer
- cloud deployment
- rate limiting

---

# Current Stable Checkpoint

```text
Patient API               COMPLETE
Screening API             COMPLETE
Business rules            COMPLETE
PostgreSQL                COMPLETE
SQLAlchemy                COMPLETE
Alembic                   COMPLETE
Router refactor           COMPLETE
Automated tests           21 PASSING
Docker                    NEXT
GitHub Actions            AFTER DOCKER
Portfolio V1              CLOSE TO COMPLETE
```

The next engineering task is:

```text
Dockerize FastAPI + PostgreSQL
```
