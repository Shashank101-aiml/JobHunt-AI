# Pytest + Requests Backend API Automation Guide — JobHunt-AI

This document provides technical documentation on the automated backend API test suite implemented using Pytest and Requests.

---

## 1. Overview & Tooling

The API automation suite executes HTTP requests against a running FastAPI backend, validating real database operations and vector store integrations without mocking core endpoints:
- Python `requests` v2.32+
- `pytest` v9.1+ with `pytest-asyncio`, `pytest-cov`, and `pytest-html`
- Custom `APITestClient` with latency monitoring
- Fixture lifecycle management for active resumes and seeded jobs

---

## 2. API Test Suites (`tests/api/`)

| Test Suite File | Routes Covered | Key Tests | Status |
| :--- | :--- | :--- | :---: |
| [`test_core_api.py`](file:///d:/Job-hunt/tests/api/test_core_api.py) | `GET /health`, `GET /api/v1/dashboard/stats` | Status codes, health keys, CORS headers, latency < 0.5s. | 4/4 Passed |
| [`test_resumes_api.py`](file:///d:/Job-hunt/tests/api/test_resumes_api.py) | `POST /api/v1/resumes`, `GET /api/v1/resumes`, `GET /api/v1/resumes/active`, `POST /api/v1/resumes/{id}/activate`, `DELETE /api/v1/resumes/{id}` | Multi-format upload, parsed skills, structured profiles, activation lifecycle, format rejection, deletion. | 13/13 Passed |
| [`test_jobs_api.py`](file:///d:/Job-hunt/tests/api/test_jobs_api.py) | `POST /api/v1/jobs/manual`, `POST /api/v1/jobs/scrape`, `GET /api/v1/jobs`, `GET /api/v1/jobs/{id}` | Manual ingestion, canonical URL deduplication, short JD rejection, botwall protection (LinkedIn/Indeed), pagination & search. | 11/11 Passed |
| [`test_ats_matching_api.py`](file:///d:/Job-hunt/tests/api/test_ats_matching_api.py) | `POST /api/v1/match/evaluate` | Formula calculation, subscores verification, role discrimination (high vs low role score separation), 400/404 handling. | 6/6 Passed |
| [`test_applications_api.py`](file:///d:/Job-hunt/tests/api/test_applications_api.py) | `POST /api/v1/apply`, `GET /api/v1/status/{id}`, `GET /api/v1/applications`, `POST /api/v1/applications/{id}/review`, `PATCH /api/v1/applications/{id}`, `POST /api/v1/applications/{id}/submit`, `GET /api/v1/applications/{id}/events`, `GET /api/v1/applications/{id}/download-docx` | Synchronous pipeline execution, duplicate prevention, candidate review persistence, status transitions, confirmation enforcement, audit events, binary DOCX export. | 13/13 Passed |
| [`test_security_resilience_api.py`](file:///d:/Job-hunt/tests/api/test_security_resilience_api.py) | Various | SQL injection parameterization immunity, XSS tag sanitization, Unicode/multilingual/emoji robustness, 405 Method Not Allowed, 422 malformed JSON. | 6/6 Passed |

---

## 3. SLA & Performance Benchmarks

All endpoints enforce latency budgets tested via `response.latency_seconds`:
- **Health Checks:** < 0.50s (actual: ~0.003s)
- **Standard CRUD (Jobs, Resumes, Applications):** < 2.0s (actual: ~0.01s - 0.05s)
- **Synchronous AI Tailoring Pipeline:** < 5.0s (actual: ~0.8s - 1.4s)
- **DOCX Generation & Binary Download:** < 1.0s (actual: ~0.02s - 0.04s)

---

## 4. Execution Commands

```bash
# 1. Start FastAPI Backend Server
uvicorn app.main:app --host 127.0.0.1 --port 8000

# 2. Run API Test Suite with HTML Report
pytest tests/api/ -v --html=docs/reports/api_test_report.html --self-contained-html

# 3. Run Specific Suite (e.g. Security & Resilience)
pytest tests/api/test_security_resilience_api.py -v
```
