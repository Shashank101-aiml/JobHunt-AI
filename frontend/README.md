# Job Hunt AI — Frontend Studio

A modern, responsive React + TypeScript + Vite + Tailwind CSS dashboard that integrates directly with the Job Hunt FastAPI backend.

---

## 1. Features & Implemented Pages

- **Dashboard (`/`)**: Displays live aggregated statistics (Total Jobs, Applications Tracked, Awaiting Review, Submitted, Average ATS Score), application status distribution bar chart, quick actions, and recent jobs/applications.
- **Resume Manager (`/resumes`)**: Drag-and-drop and standard file picker for `.pdf`, `.docx`, and `.txt` candidate resumes with pre-upload size (<10MB) and format validation. Shows extracted candidate contact info, 200+ skill taxonomy chips, active resume toggle, and an inspect profile modal.
- **Job Discovery (`/jobs`)**: Dual ingestion modes:
  1. *Manual Job Input*: Direct input for jobs behind CAPTCHAs, paywalls, or login portals (e.g., LinkedIn).
  2. *URL Scraper*: Automated parsing for official Greenhouse (`boards.greenhouse.io`) and Lever (`api.lever.co`) APIs, as well as permitted direct URLs.
  Includes search, location filter, pagination, and job details inspector.
- **Match & ATS Analysis (`/match`)**: Select a candidate resume and evaluate against a saved job or custom pasted job description. Renders transparent 5-factor weighted ATS scores (Required Skills: 40%, Preferred Skills: 15%, Experience Alignment: 20%, Keyword Density: 15%, Section Completeness: 10%), matched vs. missing skills chips, and actionable recommendations.
- **Resume Tailoring Studio (`/tailor`)**: Injects retrieved ChromaDB chunks, enforces anti-hallucination guardrails, and renders a live side-by-side editable preview of the tailored resume and customized cover letter. Calculates before/after ATS scores, saves manual edits, and exports directly to Microsoft Word `.docx`.
- **Application Tracker (`/applications`)**: Comprehensive dashboard tracking honest application states (`draft`, `ready_for_review`, `requires_manual_action`, `submitted`, `interviewing`, `rejected`, `offer`). Features status filter, keyword search, inline status updates, and links to final review.
- **Application Review & Submission (`/applications/:id/review`)**: Dedicated human-in-the-loop review screen before any external action. Includes a mandatory verification checklist, editable resume/cover letter, employer portal launch button, and confirmation handler.
- **Settings & Diagnostics (`/settings`)**: Real-time diagnostic monitors for PostgreSQL/SQLite database layer, ChromaDB vector store collection counts, LLM provider configuration status, and SMTP email service.

---

## 2. Technology Stack

- **Framework**: React 19 + TypeScript + Vite
- **Styling**: Tailwind CSS v3 + PostCSS + Autoprefixer
- **Routing**: React Router v7
- **HTTP Client**: Axios with centralized error formatting and timeout bounds
- **Icons**: Lucide React
- **Visualizations**: Recharts
- **Validation**: Zod + React Hook Form

---

## 3. Environment Variables

Create `.env` in `frontend/` (template provided in `frontend/.env.example`):

```bash
# FastAPI Backend URL
VITE_API_BASE_URL=http://localhost:8000
```

---

## 4. Local Development on Windows

### Step 1: Install Dependencies
```powershell
cd frontend
npm install --legacy-peer-deps
```

### Step 2: Start Development Server
```powershell
npm run dev
```
The frontend will be available at: **`http://localhost:5173`**

### Step 3: Run Production Build
```powershell
npm run build
```

### Step 4: Run Code Quality Checks
```powershell
npm run lint
```
