# Pytest + Requests Backend API Automation Report — JobHunt-AI

**Date:** 2026-11-06  
**Framework:** Pytest 9.1+ with Requests 2.32+ and `pytest-html` 4.2+  
**Target Environment:** Running FastAPI Service on `http://127.0.0.1:8000` (SQLite + ChromaDB Vector Store)  
**HTML Report:** [`docs/reports/api_test_report.html`](file:///d:/Job-hunt/docs/reports/api_test_report.html)  

---

## 1. Executive Summary

| Metric | Result |
| :--- | :--- |
| **Total API Tests Automated** | 53 tests |
| **Passed Tests** | **53 (100%)** |
| **Failed Tests** | 0 |
| **Skipped Tests** | 0 |
| **Total Execution Duration** | 13.15s |
| **Overall Backend Test Suite** | **106 tests passed (35 Unit + 18 DeepEval + 53 API)** |
| **Backend Code Coverage** | **70% Total Coverage** |
| **Status** | **PASSED (Green)** |

---

## 2. API Test Suites & Coverage Breakdown

### Suite 1: Core Health & Infrastructure (`tests/api/test_core_api.py`)
| Test Name | Method & Route | Verified Assertions | Status | Latency |
| :--- | :--- | :--- | :---: | :---: |
| `test_health_check_status_and_keys` | `GET /health` | Status 200, Content-Type JSON, payload keys (`status="ok"`, `service`, `database="ok"`, `vector_store`, `llm_provider`, `email_service`) | **PASS** | 0.004s |
| `test_health_check_response_latency` | `GET /health` | Status 200, response time within strict < 0.5s SLA budget | **PASS** | 0.003s |
| `test_cors_headers_handling` | `GET /health` | Origin header handled, `Access-Control-Allow-Origin` surfaced | **PASS** | 0.004s |
| `test_dashboard_stats_endpoint` | `GET /api/v1/dashboard/stats` | Status 200, aggregated metrics (`total_jobs`, `total_applications`, `awaiting_review`, `submitted`, `interviewing`, `status_distribution`) | **PASS** | 0.012s |

### Suite 2: Candidate Resume API (`tests/api/test_resumes_api.py`)
| Test Name | Method & Route | Verified Assertions | Status |
| :--- | :--- | :--- | :---: |
| `test_upload_valid_txt_resume` | `POST /api/v1/resumes` | Uploads `.txt`, verifies NLP entity extraction, parsed skills, structured profile | **PASS** |
| `test_upload_valid_docx_resume` | `POST /api/v1/resumes` | Uploads `.docx`, verifies XML extraction, MIME type, `is_active=False` | **PASS** |
| `test_upload_valid_pdf_resume` | `POST /api/v1/resumes` | Uploads `.pdf`, verifies PDF text extraction and byte size | **PASS** |
| `test_reject_unsupported_file_extension` | `POST /api/v1/resumes` | Uploads `.jpg`, enforces HTTP 400 with unsupported format error detail | **PASS** |
| `test_reject_empty_zero_byte_file` | `POST /api/v1/resumes` | Uploads 0-byte file, enforces HTTP 400 empty file rejection | **PASS** |
| `test_reject_missing_file_payload` | `POST /api/v1/resumes` | Sends empty request without multipart file, enforces HTTP 422 | **PASS** |
| `test_list_resumes` | `GET /api/v1/resumes` | Status 200, list schema match, latency < 2.0s | **PASS** |
| `test_get_active_resume` | `GET /api/v1/resumes/active` | Status 200, returns active candidate resume | **PASS** |
| `test_get_resume_by_id` | `GET /api/v1/resumes/{id}` | Status 200, returns correct candidate record | **PASS** |
| `test_get_resume_not_found_404` | `GET /api/v1/resumes/999999` | Non-existent ID returns HTTP 404 with error detail | **PASS** |
| `test_activate_resume_lifecycle` | `POST /api/v1/resumes/{id}/activate` | Updates active state, deactivates previous resume, reflects in `/active` | **PASS** |
| `test_activate_non_existent_resume_404`| `POST /api/v1/resumes/999999/activate` | Non-existent ID returns HTTP 404 | **PASS** |
| `test_delete_resume_and_cleanup` | `DELETE /api/v1/resumes/{id}` | Status 200, deletes DB entry and vector index, confirms 404 on subsequent get | **PASS** |

### Suite 3: Job Ingestion & Normalization API (`tests/api/test_jobs_api.py`)
| Test Name | Method & Route | Verified Assertions | Status |
| :--- | :--- | :--- | :---: |
| `test_create_manual_job_success` | `POST /api/v1/jobs/manual` | Creates manual job, verifies regex/taxonomy parser extracts structured JD requirements | **PASS** |
| `test_create_manual_job_canonical_url_deduplication` | `POST /api/v1/jobs/manual` | Normalizes URL and prevents duplicate records in DB | **PASS** |
| `test_reject_manual_job_too_short` | `POST /api/v1/jobs/manual` | Text < 20 characters returns HTTP 400 with validation message | **PASS** |
| `test_reject_manual_job_missing_description` | `POST /api/v1/jobs/manual` | Missing description field returns HTTP 422 Unprocessable Entity | **PASS** |
| `test_scrape_job_restricted_domain_linkedin` | `POST /api/v1/jobs/scrape` | Rejects `linkedin.com` with HTTP 403 Forbidden and platform barrier detail | **PASS** |
| `test_scrape_job_restricted_domain_indeed` | `POST /api/v1/jobs/scrape` | Rejects `indeed.com` with HTTP 403 Forbidden | **PASS** |
| `test_scrape_job_malformed_url_422` | `POST /api/v1/jobs/scrape` | Non-HTTP URL returns HTTP 422 | **PASS** |
| `test_list_jobs_with_pagination` | `GET /api/v1/jobs` | Pagination parameters `skip=0&limit=5`, returns `total` and `items` array | **PASS** |
| `test_list_jobs_with_keyword_search` | `GET /api/v1/jobs` | Filter by `search` term across title and company | **PASS** |
| `test_get_job_by_id` | `GET /api/v1/jobs/{id}` | Status 200, returns full job record with `structured_jd` | **PASS** |
| `test_get_job_not_found_404` | `GET /api/v1/jobs/999999` | Non-existent ID returns HTTP 404 | **PASS** |

### Suite 4: ATS Scoring & Compatibility Evaluation API (`tests/api/test_ats_matching_api.py`)
| Test Name | Method & Route | Verified Assertions | Status |
| :--- | :--- | :--- | :---: |
| `test_evaluate_match_with_saved_job_id` | `POST /api/v1/match/evaluate` | Evaluates against saved job; validates 5 subscores (Required 40%, Preferred 15%, YoE 20%, Keywords 15%, Completeness 10%) | **PASS** |
| `test_evaluate_match_with_custom_job_text` | `POST /api/v1/match/evaluate` | Evaluates direct JD string without prior database ingestion | **PASS** |
| `test_evaluate_match_discriminates_mismatched_roles` | `POST /api/v1/match/evaluate` | Compares high-alignment vs low-alignment roles (verifies > 15pt score separation) | **PASS** |
| `test_evaluate_match_rejects_empty_target` | `POST /api/v1/match/evaluate` | Missing both job_id, job_text, and job_url returns HTTP 400 | **PASS** |
| `test_evaluate_match_invalid_job_id_404` | `POST /api/v1/match/evaluate` | Non-existent job ID returns HTTP 404 | **PASS** |
| `test_evaluate_match_invalid_resume_id_404` | `POST /api/v1/match/evaluate` | Non-existent resume ID returns HTTP 404 | **PASS** |

### Suite 5: Application Lifecycle & Export API (`tests/api/test_applications_api.py`)
| Test Name | Method & Route | Verified Assertions | Status |
| :--- | :--- | :--- | :---: |
| `test_trigger_application_sync_execution` | `POST /api/v1/apply` | Executes tailoring pipeline synchronously; produces tailored resume, cover letter, score | **PASS** |
| `test_application_duplicate_prevention` | `POST /api/v1/apply` | Prevents duplicate applications for same resume + job pair | **PASS** |
| `test_list_applications_and_filtering` | `GET /api/v1/applications` | Filters by `status=ready_for_review`, verifies pagination schema | **PASS** |
| `test_get_application_by_id` | `GET /api/v1/applications/{id}` | Status 200, returns complete application entity | **PASS** |
| `test_get_application_status_lightweight` | `GET /api/v1/status/{id}` | Lightweight status polling endpoint responds in < 1.0s | **PASS** |
| `test_get_application_not_found_404` | `GET /api/v1/applications/999999` | Non-existent application returns HTTP 404 | **PASS** |
| `test_save_application_review_edits` | `POST /api/v1/applications/{id}/review` | Persists edited resume text, cover letter, and notes; logs `review_updated` audit event | **PASS** |
| `test_patch_application_status_lifecycle` | `PATCH /api/v1/applications/{id}` | Updates status to `interviewing`; rejects invalid status with HTTP 400 | **PASS** |
| `test_submit_application_without_confirmation` | `POST /api/v1/applications/{id}/submit` | `candidate_confirmed=False` transitions status to `requires_manual_action` | **PASS** |
| `test_submit_application_with_confirmation` | `POST /api/v1/applications/{id}/submit` | `candidate_confirmed=True` marks `submitted` and records timestamp | **PASS** |
| `test_get_application_audit_events` | `GET /api/v1/applications/{id}/events` | Returns chronological event logs (`event_type`, `message`, `created_at`) | **PASS** |
| `test_download_tailored_docx_endpoint` | `GET /api/v1/applications/{id}/download-docx` | FileResponse with OpenXML MIME type, filename header, and binary magic `PK\x03\x04` | **PASS** |
| `test_download_docx_not_found_404` | `GET /api/v1/applications/999999/download-docx` | Non-existent application returns HTTP 404 | **PASS** |

### Suite 6: Security, Resilience & Boundary Testing (`tests/api/test_security_resilience_api.py`)
| Test Name | Target Route | Boundary / Attack Vector | Status |
| :--- | :--- | :--- | :---: |
| `test_sql_injection_resilience_in_search_query` | `GET /api/v1/jobs` | Injects `' OR '1'='1'; DROP TABLE jobs; --` in query string; safely parameterized without 500 error | **PASS** |
| `test_sql_injection_resilience_in_body_parameters`| `POST /api/v1/jobs/manual` | Injects SQL DDL in JSON body; stored as literal escaped text; table intact | **PASS** |
| `test_xss_script_injection_sanitization` | `POST /api/v1/jobs/manual` | Injects `<script>` and `<img>` tags; stored safely without unhandled error | **PASS** |
| `test_unicode_and_special_character_resilience` | `POST /api/v1/jobs/manual` | Multi-script multilingual text (French, Japanese, Arabic, Emojis 🚀) preserved | **PASS** |
| `test_malformed_json_body_returns_422` | `POST /api/v1/jobs/manual` | Truncated/broken JSON payload returns HTTP 422 Unprocessable Entity | **PASS** |
| `test_invalid_http_method_returns_405` | `DELETE /health` | Invalid HTTP method on read-only route returns HTTP 405 Method Not Allowed | **PASS** |

---

## 3. SLA & Performance Adherence

- **Core / Health Checks:** ~0.003s – 0.005s (SLA < 0.5s)
- **CRUD Operations (Jobs, Resumes, Applications):** ~0.01s – 0.05s (SLA < 2.0s)
- **Synchronous AI Tailoring & Vector Search:** ~0.8s – 1.4s (SLA < 5.0s)
- **DOCX Generation & Binary Streaming:** ~0.02s – 0.04s (SLA < 1.0s)
