# Playwright Browser End-to-End Testing Guide — JobHunt-AI

This document outlines the architecture, Page Object Models, test fixtures, and execution procedures for the Playwright browser test suite.

---

## 1. Overview & Tooling

The Playwright test suite automates end-to-end browser journeys across the React frontend and FastAPI backend using:
- `@playwright/test` v1.56+
- Chromium Headless Browser Engine
- Page Object Model (POM) Design Pattern
- Synthetic Multi-Format Resume Fixtures (PDF, DOCX, TXT)
- HTML reporting, video capture, and failure screenshots

---

## 2. Page Object Models (`frontend/e2e/pages/`)

| Page Object Model | Target Page / Route | Key Encapsulated Interactions |
| :--- | :--- | :--- |
| [`BasePage.ts`](file:///d:/Job-hunt/frontend/e2e/pages/BasePage.ts) | Shared Shell | Navigation links, alert banners (`div.rounded-xl.bg-emerald-50`, `bg-rose-50`), loading spinners. |
| [`ResumesPage.ts`](file:///d:/Job-hunt/frontend/e2e/pages/ResumesPage.ts) | `/resumes` | File dropzone, format filtering, resume activation, deletion. |
| [`JobsPage.ts`](file:///d:/Job-hunt/frontend/e2e/pages/JobsPage.ts) | `/jobs` | Tab navigation (Browse, Manual Input, Scrape URL), manual form submission, scraper modal. |
| [`MatchPage.ts`](file:///d:/Job-hunt/frontend/e2e/pages/MatchPage.ts) | `/match` | Target resume & JD selection, ATS score ring display, subscore breakdown cards, recommendations. |
| [`TailorPage.ts`](file:///d:/Job-hunt/frontend/e2e/pages/TailorPage.ts) | `/tailor` | Tailoring pipeline execution, before/after score diff, dual-column markdown/text editors, DOCX export. |
| [`ApplicationReviewPage.ts`](file:///d:/Job-hunt/frontend/e2e/pages/ApplicationReviewPage.ts) | `/applications/{id}/review` | 3 mandatory human review checkboxes, submission options (manual portal, email), audit trail timeline. |
| [`ApplicationsPage.ts`](file:///d:/Job-hunt/frontend/e2e/pages/ApplicationsPage.ts) | `/applications` | Application list cards, lifecycle status filters (`ready_for_review`, `submitted`, etc.). |

---

## 3. Test Fixtures (`frontend/e2e/fixtures/test_resumes/`)

- `sample_backend_resume.txt` — Plain text backend engineer resume.
- `sample_fullstack_resume.docx` — Microsoft Word formatted full-stack engineer resume.
- `sample_resume.pdf` — Valid PDF resume document.
- `empty_resume.txt` — 0-byte file for upload validation.
- `invalid_file.jpg` — Unsupported format for file filter validation.

---

## 4. Test Specifications & Coverage

| Specification File | Workflow Name | Tests | Focus |
| :--- | :--- | :---: | :--- |
| `01_resume_management.spec.ts` | Candidate Resume Management | 5 | PDF, DOCX, TXT uploads; JPG rejection; empty file rejection. |
| `02_job_submission.spec.ts` | Job Discovery & Submission | 3 | Manual JD input, length validation (< 20 chars), LinkedIn scraper boundary alert. |
| `03_ats_evaluation.spec.ts` | ATS Compatibility Evaluation | 2 | Score ring display, subscore weighting, actionable recommendations. |
| `04_resume_tailoring.spec.ts` | AI Resume Tailoring | 2 | Dual-column generation (resume + cover letter), input validation. |
| `05_application_review.spec.ts` | Human-in-the-Loop Review | 1 | Mandatory 3 review checkboxes, manual edit persistence, status transition to `submitted`. |
| `06_docx_download.spec.ts` | Tailored Resume Export | 1 | Intercepts download stream, checks `.docx` extension, asserts file size > 1000 bytes. |
| `07_error_handling.spec.ts` | Error & Resilience Boundaries | 3 | Route abort for network drops, 500 error display, 404 application review route boundary. |

---

## 5. Execution Commands

```bash
# Start FastAPI Backend
uvicorn app.main:app --host 127.0.0.1 --port 8000

# In frontend directory:
cd frontend

# Run all Playwright E2E tests headless
npx playwright test

# Run tests in interactive UI mode
npx playwright test --ui

# Run specific specification
npx playwright test e2e/specs/01_resume_management.spec.ts
```
