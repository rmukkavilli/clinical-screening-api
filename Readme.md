cd C:\Users\ravir\OneDrive\Desktop\pytest-fhir\rmukkavilli\clinical-screening-api

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

.\.venv\Scripts\Activate.ps1

python -m pytest

fastapi dev app\main.py