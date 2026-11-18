# JobHunt-AI Unified Testing & Quality Engineering Strategy

This document outlines the testing architecture, standards, test suite composition, and execution procedures for JobHunt-AI across all four layers of the test pyramid.

---

## 1. Quality Architecture Overview

JobHunt-AI implements a four-tier automated testing strategy designed to provide high confidence across deterministic application code, browser user workflows, REST API contracts, and non-deterministic LLM generations.

```
                    ┌────────────────────────────┐
                    │   LLM Evaluation (DeepEval)│  18 Scenarios (100% Pass)
                    ├────────────────────────────┤
                    │    Playwright E2E Tests    │  17 Workflows (100% Pass)
                    ├────────────────────────────┤
                    │ Pytest + Requests API Tests│  53 Endpoints (100% Pass)
                    ├────────────────────────────┤
                    │  Unit & Integration Tests  │  35 Tests (100% Pass)
                    └────────────────────────────┘
```

---

## 2. Test Suite Composition & Locations

| Layer | Directory | Test Files | Count | Purpose |
| :--- | :--- | :--- | :---: | :--- |
| **Layer 1: Unit & Integration** | `tests/` | `test_resume_parser.py`, `test_jd_parser.py`, `test_vector_store.py`, `test_ats_scorer.py`, `test_tailor.py`, `test_submission.py`, `test_pipeline.py`, `test_api_endpoints.py`, `test_scraper.py`, `test_scrapers.py` | 35 | Verifies parsing algorithms, embedding math, state graph orchestration, and scoring logic. |
| **Layer 2: Backend API Automation** | `tests/api/` | `test_core_api.py`, `test_resumes_api.py`, `test_jobs_api.py`, `test_ats_matching_api.py`, `test_applications_api.py`, `test_security_resilience_api.py` | 53 | Exercises live FastAPI endpoints against real SQLite database, validating HTTP codes, latency SLAs, headers, and injection resilience. |
| **Layer 3: Playwright Browser E2E** | `frontend/e2e/specs/` | `01_resume_management.spec.ts` through `07_error_handling.spec.ts` | 17 | Drives real Chromium browser sessions against the React frontend and FastAPI backend, testing user journeys, file uploads, dual-column editing, and human checklist confirmation. |
| **Layer 4: DeepEval LLM Evaluation** | `tests/eval/` | `test_deepeval_metrics.py`, `test_safety_adversarial.py`, `test_schema_validation.py`, `run_evaluation.py` | 18 | Measures faithfulness, hallucination, JD alignment, schema conformance, and adversarial injection resistance across 18 synthetic candidate profiles. |

---

## 3. Test Execution Procedures

### 3.1 Running Unit & Integration Tests
```bash
pytest tests/test_*.py -v --cov=app --cov-report=term-missing
```

### 3.2 Running Backend API Automation
Requires the FastAPI backend running on port 8000:
```bash
# Terminal 1:
uvicorn app.main:app --host 127.0.0.1 --port 8000

# Terminal 2:
pytest tests/api/ -v --html=docs/reports/api_test_report.html --self-contained-html
```

### 3.3 Running Playwright Browser End-to-End Tests
Requires both FastAPI backend and Vite frontend running (Playwright webServer automatically handles Vite if configured):
```bash
# Terminal 1:
uvicorn app.main:app --host 127.0.0.1 --port 8000

# Terminal 2:
cd frontend
npx playwright test
```

### 3.4 Running DeepEval LLM Evaluation Runner
```bash
python tests/eval/run_evaluation.py
```

### 3.5 Running Unified Pytest Suite (106 Tests)
```bash
pytest -v --cov=app --cov-report=term-missing
```

---

## 4. Test Reporting & Artifacts

- **Unit Test Coverage:** Generated via `pytest-cov`, outputting terminal breakdown and `coverage.xml`.
- **API Automation Report:** Self-contained interactive HTML report at [`docs/reports/api_test_report.html`](reports/api_test_report.html) and summary at [`docs/reports/api_automation_report.md`](reports/api_automation_report.md).
- **Playwright E2E Report:** Interactive HTML report at `docs/reports/playwright-report/` and markdown summary at [`docs/reports/playwright_e2e_report.md`](reports/playwright_e2e_report.md).
- **DeepEval Evaluation Report:** JSON and markdown reports at [`docs/reports/deepeval_evaluation_report.md`](reports/deepeval_evaluation_report.md) and [`docs/reports/deepeval_evaluation_report.json`](reports/deepeval_evaluation_report.json).
