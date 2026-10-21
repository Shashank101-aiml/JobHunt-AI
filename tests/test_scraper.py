import pytest
from app.agents.scraper_agent import scrape_job

def test_scrape_job_with_manual_text():
    state = {
        "job_text": "Title: Lead Python Engineer\nCompany: DataForge\nRequirements:\n- 4+ years Python, FastAPI\n- Docker, AWS",
        "job_url": ""
    }
    res = scrape_job(state)
    assert res["status"] == "scraping_complete"
    assert "raw_jd" in res
    assert res["structured_jd"]["title"] == "Lead Python Engineer"
    assert "Python" in res["structured_jd"]["required_skills"]

def test_scrape_job_restricted_domain_fails_honestly():
    state = {"job_url": "https://www.linkedin.com/jobs/view/99999"}
    res = scrape_job(state)
    assert res["status"] == "failed"
    assert "error" in res
    assert "restricted" in res["error"].lower()

def test_scrape_job_empty_fails_honestly():
    state = {"job_url": "", "job_text": ""}
    res = scrape_job(state)
    assert res["status"] == "failed"
    assert "error" in res
