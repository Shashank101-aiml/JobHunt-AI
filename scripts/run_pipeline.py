import argparse
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SyncSessionLocal, Base, sync_engine
from app.models.application import Application, ApplicationEvent
from app.models.resume import Resume
from app.orchestrator.runner import run_pipeline_sync

def main():
    parser = argparse.ArgumentParser(description="Trigger end-to-end Job Hunt Pipeline CLI")
    parser.add_argument("--url", default=None, help="Target Job Posting URL")
    parser.add_argument("--text", default=None, help="Direct Job Description text")
    parser.add_argument("--jd_file", default=None, help="Path to text file containing Job Description")
    parser.add_argument("--resume_id", type=int, default=None, help="Resume ID (defaults to active resume)")
    args = parser.parse_args()

    Base.metadata.create_all(bind=sync_engine)

    db = SyncSessionLocal()
    try:
        # Resolve Resume
        res = None
        if args.resume_id:
            res = db.query(Resume).filter(Resume.id == args.resume_id).first()
        if not res:
            res = db.query(Resume).filter(Resume.is_active == True).order_by(Resume.created_at.desc()).first()
        if not res:
            res = db.query(Resume).order_by(Resume.created_at.desc()).first()

        if not res:
            print("Error: No candidate resume found in database. Run 'python scripts/seed_resume.py' first.")
            sys.exit(1)

        job_text = args.text
        if args.jd_file:
            if not os.path.exists(args.jd_file):
                print(f"Error: Job description file '{args.jd_file}' not found.")
                sys.exit(1)
            with open(args.jd_file, "r", encoding="utf-8") as f:
                job_text = f.read()

        if not args.url and not job_text:
            print("Error: Please provide either --url, --text, or --jd_file.")
            sys.exit(1)

        job_url = args.url or f"manual-cli-input-{len(job_text or '')}"

        res_id = res.id
        res_filename = res.filename

        # Create Application record
        app_db = Application(
            job_url=job_url,
            resume_id=res_id,
            status="draft"
        )
        db.add(app_db)
        db.commit()
        db.refresh(app_db)
        app_id = app_db.id
    finally:
        db.close()

    print(f"\n==================================================")
    print(f"Starting Job Hunt Pipeline for Application ID: {app_id}")
    print(f"Using Resume: {res_filename} (ID: {res_id})")
    print(f"Job Target: {args.url or 'Manual JD Text'}")
    print(f"==================================================\n")

    result = run_pipeline_sync(
        app_id=app_id,
        job_url=args.url,
        job_text=job_text,
        resume_id=res_id
    )

    if result.get("error"):
        print(f"\n[FAILED] Pipeline encountered an error:")
        print(f"Reason: {result['error']}")
        sys.exit(1)

    structured = result.get("structured_jd", {})
    feedback = result.get("ats_feedback", {})
    diff = result.get("tailored_diff", {})

    print(f"[SUCCESS] Pipeline Completed!")
    print(f"- Job Title: {structured.get('title', 'Unknown')}")
    print(f"- Company: {structured.get('company', 'Not specified')}")
    print(f"- Overall ATS Score: {result.get('ats_score', 0)} / 100")
    if feedback and "subscores" in feedback:
        sub = feedback["subscores"]
        print(f"  * Required Skills Match: {sub.get('required_skills_match')}%")
        print(f"  * Preferred Skills Match: {sub.get('preferred_skills_match')}%")
        print(f"  * Experience Alignment: {sub.get('experience_match')}%")
        print(f"  * Keyword Density: {sub.get('keyword_density')}%")
    print(f"- Matched Skills ({len(feedback.get('matched_skills', []))}): {', '.join(feedback.get('matched_skills', [])[:6])}")
    print(f"- Missing Requirements: {', '.join(feedback.get('missing_skills', [])) or 'None'}")
    print(f"- Tailoring Mode: {diff.get('mode', 'standard')}")
    print(f"- Application Status: {result.get('status')}")
    print(f"\nApplication record saved. Review package ready in database (Application ID: {app_id}).")

if __name__ == "__main__":
    main()
