# Job Hunt: Real-World AI Job Search & Application Platform

A reliable, evidence-based AI platform that ingests real candidate resumes, parses live job descriptions, generates dense vector embeddings via ChromaDB, performs transparent ATS scoring, produces factually grounded tailored resumes, and tracks applications honestly through explicit human-in-the-loop workflows.

---

## 1. What the Application Actually Does

Job Hunt is **not** a placeholder demo or mock scraper. It provides complete, verified pipelines for real-world job hunting:

- **Multi-Format Resume Ingestion**: Ingests real PDF, DOCX, and TXT files. Deterministically parses contact info (email, phone, LinkedIn, GitHub), categorizes 200+ industry skills, chunks experience and education, and saves both raw and normalized JSON profiles to PostgreSQL / SQLite.
- **Dynamic Job Description Ingestion**: Extracts job titles, company names, work model (remote/hybrid/onsite), minimum years of experience, salary ranges, required vs. preferred qualifications, and keywords from unstructured text or URLs without hardcoded assumptions.
- **Modular Job Scraper Subsystem**: Supports official REST APIs (Greenhouse `boards-api.greenhouse.io`, Lever `api.lever.co`), permitted direct URLs, and manual input. Enforces robots.txt / domain restrictions (`RestrictedJobSourceError`) to prevent unauthorized scraping of login-walled or anti-bot protected sites like LinkedIn.
- **Dense ChromaDB Semantic Embeddings**: Uses local ONNX-powered `all-MiniLM-L6-v2` dense vectors (384 dimensions) to index resume experiences and retrieve top-k semantically relevant chunks for any job requirement. Operates 100% offline with zero API key dependencies.
- **Transparent ATS Compatibility Scorer**: Evaluates resumes against JDs using a documented weighted formula (Required Skills: 40%, Preferred Skills: 15%, Experience Alignment: 20%, Keyword Density: 15%, Section Completeness: 10%). Produces transparent subscore breakdowns, evidence citations, and actionable recommendations.
- **Factual Resume Tailoring**: Employs strict anti-hallucination guardrails. Never invents employers, dates, metrics, or degrees. Injects retrieved ChromaDB context into LLM prompts (Anthropic Claude or OpenAI) and exports tailored resumes directly to `.docx`. Provides an offline heuristic alignment fallback if an LLM is unconfigured.
- **Personalized Cover Letters**: Crafts customized cover letters based exclusively on documented candidate achievements.
- **Honest Application Tracking & Submissions**: Distinguishes application tracking from external submission. Supports manual portal packages (providing review checklists and candidate confirmation) and verified SMTP email submissions. Applications transition to `ready_for_review` before any external action, and are only marked `submitted` upon verified delivery or candidate confirmation.
- **Resilient Database Layer**: SQLAlchemy async/sync models with Alembic migrations. Gracefully connects to PostgreSQL in Docker or falls back automatically to local SQLite for instant zero-dependency local development.

---

## 2. Architecture & Data Flow

```
[Candidate Resume (PDF/DOCX/TXT)]
       │
       ▼
 [Resume Parser Service]
       │
       ├────────────────────────────────────────┐
       ▼                                        ▼
[PostgreSQL / SQLite Database]       [ChromaDB Local Vector Store]
(Structured Profile & Text)          (Dense ONNX Embeddings - 384d)
       │                                        │
       ▼                                        ▼
 [Job Source Discovery]               [Semantic Chunk Retrieval]
 (Greenhouse / Lever / Direct / Manual)         │
       │                                        │
       ▼                                        │
 [JD Parser & Normalizer]                       │
       │                                        │
       ├────────────────────────────────────────┘
       ▼
 [ATS Evidence Scorer] ──► (Transparent 5-Factor Score & Suggestions)
       │
       ▼
 [Resume Tailor & Cover Letter Engine] ──► (Anti-Hallucination Guardrails + DOCX Export)
       │
       ▼
 [LangGraph Orchestrator] ──► Status: 'ready_for_review'
       │
       ▼ (Human in the loop review)
 [Submission Adapter Architecture]
   ├── Manual Portal Adapter (Requires Candidate Confirmation)
   └── SMTP Email Adapter (Requires Verified Delivery)
       │
       ▼
 [Application Audit Events Log] ──► Status: 'submitted' / 'requires_manual_action'
```

---

## 3. Supported Job Sources & Boundaries

| Source | Retrieval Mechanism | Policy & Restrictions | Status |
| :--- | :--- | :--- | :--- |
| **Greenhouse** | Official REST API (`boards-api.greenhouse.io`) | Permitted public job board API | Fully Functional |
| **Lever** | Official REST API (`api.lever.co/v0/postings`) | Permitted public job board API | Fully Functional |
| **Direct URLs** | HTTPX + BeautifulSoup4 | Permitted public HTML job postings | Fully Functional |
| **Manual Input** | Direct text or JSON payload | Always available when portals block scrapers | Fully Functional |
| **LinkedIn / Indeed** | **Blocked by design** | Respects Terms of Service & robots.txt; raises `RestrictedJobSourceError` | Manual Input Required |

---

## 4. Environment Variables

Create a `.env` file in the project root. A safe template is provided at `.env.example`:

```bash
# Database Configuration
# If PostgreSQL is unavailable, system automatically falls back to local SQLite (jobhunt.db)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/jobhunt
SYNC_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/jobhunt

# Redis Configuration (Optional, for Celery workers)
REDIS_URL=redis://localhost:6379/0

# Vector Store
CHROMA_PERSIST_DIRECTORY=./chroma_db

# LLM Provider Configuration
# Set LLM_PROVIDER to "anthropic" or "openai"
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-anthropic-api-key-here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Alternative: OpenAI
# LLM_PROVIDER=openai
# OPENAI_API_KEY=your-openai-api-key-here
# OPENAI_MODEL=gpt-4o

# SMTP Email Configuration (Required only for real email submissions)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@example.com
```

> **Note**: If `ANTHROPIC_API_KEY` is not provided, the tailoring service uses a deterministic **heuristic alignment mode** that highlights matching skills and formats achievements without failing or inventing fake responses.

---

## 5. Local Setup & Installation (Windows & Unix)

### Prerequisites
- Python 3.10+ (Tested on Python 3.14.2 64-bit on Windows)
- Git

### Step-by-Step Setup

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd Job-hunt
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   # On Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   # On Unix / macOS:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Prepare Environment File**:
   ```bash
   copy .env.example .env
   ```

5. **Initialize Database Migrations**:
   ```bash
   # If running with local SQLite (automatic default when Postgres is absent):
   # Tables are created automatically on launch.
   # To apply Alembic migrations against a running PostgreSQL instance:
   alembic upgrade head
   ```

---

## 6. Running with Docker Compose

To run PostgreSQL and Redis services in the background:

```bash
# Start Postgres and Redis containers
docker-compose up -d postgres redis

# Check container health
docker-compose ps
```

---

## 7. Running the Application

### Option A: Start FastAPI REST API Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive Swagger API documentation will be available at: [http://localhost:8000/docs](http://localhost:8000/docs)

### Option B: Run End-to-End CLI Pipeline
1. **Seed a Candidate Resume**:
   ```bash
   python scripts/seed_resume.py --file data/resumes/sample_resume.txt
   ```
2. **Execute Full Pipeline on a Job**:
   ```bash
   python scripts/run_pipeline.py --text "Senior Backend Engineer at Acme Corp. Required: Python, FastAPI, PostgreSQL, Docker. 5+ years experience required."
   ```

### Option C: Start React + TypeScript Frontend Studio
In a separate terminal:
```bash
cd frontend
npm install --legacy-peer-deps
npm run dev
```
Open your browser at **[http://localhost:5173](http://localhost:5173)** to access the dashboard, resume manager, job discovery, match evaluator, resume tailoring studio, and application review workflows.

---

## 8. Automated Test Suite

Run the full automated test suite containing 35 comprehensive unit and integration tests:

```bash
python -m pytest -v
```

### Test Coverage Highlights:
- `tests/test_resume_parser.py`: PDF/DOCX/TXT file reading, contact extraction, skill matching, section chunking, error handling for empty or corrupt files.
- `tests/test_jd_parser.py`: Job title, company, YOE, salary, and requirement extraction without hardcoding.
- `tests/test_vector_store.py`: Local dense ONNX embeddings verification (384 dimensions, cosine distance) and persistent ChromaDB chunk indexing.
- `tests/test_ats_scorer.py`: Evidence-based transparent ATS scoring comparing high-match vs. low-match resumes.
- `tests/test_tailor.py`: Anti-hallucination guardrails, LLM prompt engineering, and `.docx` file export.
- `tests/test_submission.py`: Manual review adapter and honest SMTP validation.
- `tests/test_pipeline.py`: Full LangGraph state transitions and early exit handling.
- `tests/test_api_endpoints.py`: FastAPI endpoints for health, resume upload, manual jobs, and application review lifecycles.

---

## 9. Key REST API Endpoints

### Health Check
- `GET /health`
  Returns real-time status of Database, ChromaDB, and LLM configuration.

### Resumes
- `POST /api/resume/upload`: Upload `.pdf`, `.docx`, or `.txt` resume.
- `GET /api/resume/list`: List all uploaded resumes.
- `POST /api/resume/{resume_id}/activate`: Set active candidate resume.
- `GET /api/resume/active`: Retrieve current active resume.

### Jobs
- `POST /api/jobs/manual`: Create a job entry directly via text.
- `POST /api/jobs/scrape`: Retrieve and parse a job from Greenhouse/Lever or permitted URL.
- `GET /api/jobs`: List ingested jobs with pagination and company/title filtering.

### Applications & Pipeline
- `POST /api/apply/trigger`: Execute end-to-end pipeline (ChromaDB retrieval -> ATS scoring -> tailoring -> cover letter).
- `GET /api/applications`: List applications with status and score filtering.
- `GET /api/applications/{app_id}`: View review package, subscores, tailored diff, and cover letter.
- `PUT /api/applications/{app_id}/review`: Candidate edits tailored resume and cover letter before submission.
- `POST /api/applications/{app_id}/submit`: Confirm manual submission or trigger authorized adapter.
- `GET /api/applications/{app_id}/download-docx`: Download the tailored resume as a `.docx` document.
- `GET /api/applications/{app_id}/events`: View chronological audit history.

---

## 10. Operational Honesty & Ethical Boundaries

1. **No Phantom Submissions**: An application is never marked `submitted` simply because an API was called. Manual portal applications stay in `requires_manual_action` until candidate confirms. Email submissions verify SMTP response.
2. **No Hallucinated Credentials**: Prompts instruct the LLM strictly to reorganize and articulate authentic candidate experiences.
3. **No Scraping Bypass**: Restricted websites (e.g. LinkedIn) are rejected cleanly, and candidates are guided to use the Manual Job Input option.
