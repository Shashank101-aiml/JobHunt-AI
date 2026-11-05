import pytest
from tests.api.conftest import APITestClient


@pytest.mark.api
class TestATSMatchingAPI:
    """ATS scoring engine, subscore breakdowns, and gap analysis evaluation endpoints."""

    def test_evaluate_match_with_saved_job_id(
        self,
        client: APITestClient,
        active_resume: dict,
        seeded_job: dict
    ):
        payload = {
            "resume_id": active_resume["id"],
            "job_id": seeded_job["id"]
        }
        response = client.post("/api/v1/match/evaluate", json=payload)
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

        data = response.json()
        assert "ats_score" in data
        assert 0 <= data["ats_score"] <= 100
        assert "feedback" in data

        feedback = data["feedback"]
        assert "subscores" in feedback
        subscores = feedback["subscores"]
        assert "required_skills_match" in subscores
        assert "preferred_skills_match" in subscores
        assert "experience_match" in subscores
        assert "keyword_density" in subscores
        assert "section_completeness" in subscores

        assert "matched_skills" in feedback
        assert "missing_skills" in feedback
        assert "suggestions" in feedback
        assert isinstance(feedback["matched_skills"], list)
        assert isinstance(feedback["suggestions"], list)

    def test_evaluate_match_with_custom_job_text(
        self,
        client: APITestClient,
        active_resume: dict
    ):
        custom_jd = (
            "Title: Senior Backend Platform Engineer\n"
            "Company: Zenith Cloud\n"
            "Requirements:\n"
            "- Python, FastAPI, Docker, PostgreSQL\n"
            "- 4+ years designing backend systems"
        )
        payload = {
            "resume_id": active_resume["id"],
            "job_text": custom_jd
        }
        response = client.post("/api/v1/match/evaluate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["job_title"] == "Senior Backend Platform Engineer"
        assert data["ats_score"] > 50

    def test_evaluate_match_discriminates_mismatched_roles(
        self,
        client: APITestClient,
        active_resume: dict
    ):
        # 1. High match JD (Python / FastAPI Backend Engineer matching candidate profile)
        python_jd = (
            "Title: Senior Python Backend Developer\n"
            "Company: TechWorks Global\n"
            "Requirements:\n"
            "- 5+ years experience in Python and FastAPI\n"
            "- Expertise with Docker, PostgreSQL, REST APIs, and SQL"
        )
        high_resp = client.post("/api/v1/match/evaluate", json={
            "resume_id": active_resume["id"],
            "job_text": python_jd
        })
        assert high_resp.status_code == 200
        high_score = high_resp.json()["ats_score"]

        # 2. Low match JD (Rust, Swift, and iOS Mobile Engineer requiring 10+ YoE absent from resume)
        mobile_jd = (
            "Title: Lead iOS and Rust Systems Engineer\n"
            "Company: MobileNative Core\n"
            "Requirements:\n"
            "- 10+ years experience in Rust, Swift, iOS, Objective-C, and Xcode\n"
            "- CocoaPods dependency management and low-level Apple metal APIs"
        )
        low_resp = client.post("/api/v1/match/evaluate", json={
            "resume_id": active_resume["id"],
            "job_text": mobile_jd
        })
        assert low_resp.status_code == 200
        low_score = low_resp.json()["ats_score"]

        # Assert clear score separation between aligned and non-aligned roles
        assert high_score > low_score + 15, f"Expected high ({high_score}) to exceed low ({low_score}) by > 15 pts"

    def test_evaluate_match_rejects_empty_target(self, client: APITestClient, active_resume: dict):
        payload = {
            "resume_id": active_resume["id"]
            # Missing job_id, job_text, and job_url
        }
        response = client.post("/api/v1/match/evaluate", json=payload)
        assert response.status_code == 400
        assert "must provide" in response.json()["detail"].lower()

    def test_evaluate_match_invalid_job_id_404(self, client: APITestClient, active_resume: dict):
        payload = {
            "resume_id": active_resume["id"],
            "job_id": 999999
        }
        response = client.post("/api/v1/match/evaluate", json=payload)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_evaluate_match_invalid_resume_id_404(self, client: APITestClient, seeded_job: dict):
        payload = {
            "resume_id": 999999,
            "job_id": seeded_job["id"]
        }
        response = client.post("/api/v1/match/evaluate", json=payload)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
