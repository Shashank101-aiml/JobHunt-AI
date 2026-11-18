# CI/CD Pipeline & Containerization Report — JobHunt-AI

**Date:** 2026-11-18  
**Component:** CI/CD Integration & Containerization (Phase 4)  
**Configuration Files:**
- [`.github/workflows/ci.yml`](file:///d:/Job-hunt/.github/workflows/ci.yml)
- [`Dockerfile`](file:///d:/Job-hunt/Dockerfile)
- [`.dockerignore`](file:///d:/Job-hunt/.dockerignore)
- [`requirements-test.txt`](file:///d:/Job-hunt/requirements-test.txt)

---

## 1. Executive Summary

Phase 4 completes the continuous integration, continuous testing, and container packaging architecture for JobHunt-AI. The workflow automates testing across all four layers of the test pyramid (Unit, API, E2E, and LLM Evaluation) along with container build verification.

| CI Job | Purpose | Dependencies | Triggers | Artifacts Generated |
| :--- | :--- | :--- | :--- | :--- |
| **`unit-tests`** | Fast unit and integration tests (35 tests) | None (runs first) | Push, PR | `coverage.xml` |
| **`api-tests`** | Pytest + Requests backend API automation (53 tests) | `unit-tests` | Push, PR | `api_test_report.html` |
| **`e2e-tests`** | Playwright browser E2E workflows (17 tests) | `unit-tests` | Push, PR | `playwright-report/`, traces |
| **`llm-eval`** | DeepEval faithfulness, hallucination & alignment evaluation (18 scenarios) | `unit-tests` | `workflow_dispatch`, `main` push, PR label | `deepeval_evaluation_report.*` |
| **`docker-build`**| Docker container image build & packaging validation | `unit-tests` | Push, PR | Docker build cache |

---

## 2. GitHub Actions Workflow Architecture (`ci.yml`)

### Fast Feedback & Dependency Graph
```
               ┌──────────────┐
               │  unit-tests  │
               └──────┬───────┘
         ┌────────────┼────────────┬─────────────┐
         ▼            ▼            ▼             ▼
    ┌─────────┐  ┌─────────┐  ┌──────────┐  ┌──────────────┐
    │api-tests│  │e2e-tests│  │ llm-eval │  │ docker-build │
    └─────────┘  └─────────┘  └──────────┘  └──────────────┘
```
1. **`unit-tests` runs first:** Fails fast within ~10 seconds if core application logic regressions are introduced, saving CI compute hours.
2. **Parallel Downstream Fanout:** `api-tests`, `e2e-tests`, `llm-eval`, and `docker-build` execute in parallel once unit tests pass.

### Controlled LLM Evaluation
- Default evaluation mode uses the deterministic `offline` judge, preventing paid external LLM provider costs during routine CI runs.
- Triggerable on demand via `workflow_dispatch` with parameter selection for model provider (`offline`, `anthropic`, `openai`).
- Enforces strict score thresholds (Faithfulness $\ge 0.85$, Hallucination $\ge 0.85$, Alignment $\ge 0.75$).

### Dependency Caching
- Python `pip` caching enabled (`cache: 'pip'`).
- Node.js `npm` caching enabled (`cache: 'npm'`, keyed to `frontend/package-lock.json`).
- Docker Buildx layer caching enabled (`type=gha`).

---

## 3. Containerization Architecture (`Dockerfile`)

### Security & Hardening Features:
1. **Minimal Base Image:** Uses `python:3.11-slim` to reduce attack surface and container footprint.
2. **Non-Root Execution:** Creates and switches to an unprivileged `appuser` (UID 1000).
3. **Healthcheck:** Configures Docker native `HEALTHCHECK` targeting `/health` endpoint (`interval=30s, timeout=5s, retries=3`).
4. **Optimized Layer Caching:** Installs system and Python requirements before copying application source code.
5. **Clean Context via `.dockerignore`:** Excludes `.git`, `.env`, `node_modules`, `tests`, `docs`, and virtual environments from image layers.

---

## 4. Verification Checklist

- [x] Root `Dockerfile` created and aligned with `docker-compose.yml` service definitions.
- [x] `.dockerignore` configured to exclude development and sensitive artifacts.
- [x] `requirements-test.txt` created with pinned test harness dependencies.
- [x] `.github/workflows/ci.yml` authored and verified as valid YAML.
- [x] All 5 jobs properly defined with dependency graph and artifact uploads.
