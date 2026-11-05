import time
import pytest
from tests.api.conftest import APITestClient


@pytest.mark.api
class TestJobsAPI:
    """Job ingestion (manual & scraper), normalization, pagination, and lookup endpoints."""

    def test_create_manual_job_success(self, client: APITestClient):
        unique_id = int(time.time() * 1000)
        payload = {
            "title": f"Lead Infrastructure Architect {unique_id}",
            "company": f"CloudVanguard {unique_id}",
            "location": "Remote / New York",
            "employment_type": "Full-Time",
            "description_text": (
                "Title: Lead Infrastructure Architect\n"
                f"Company: CloudVanguard {unique_id}\n"
                "Requirements:\n"
                "- 6+ years experience in cloud infrastructure and Terraform\n"
                "- Advanced Kubernetes cluster administration and Docker\n"
                "- Python or Go microservice development\n"
                "Responsibilities:\n"
                "- Lead cloud migration and high availability design"
            ),
            "source_url": f"https://cloudvanguard-{unique_id}.example.com/jobs/500"
        }

        response = client.post("/api/v1/jobs/manual", json=payload)
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

        data = response.json()
        assert data["id"] > 0
        assert data["title"] == payload["title"]
        assert data["company"] == payload["company"]
        assert data["source"] == "manual_entry"
        assert "structured_jd" in data
        structured = data["structured_jd"]
        assert "required_skills" in structured
        assert isinstance(structured["required_skills"], list)

    def test_create_manual_job_canonical_url_deduplication(self, client: APITestClient):
        unique_id = int(time.time() * 1000)
        source_url = f"https://dedup-{unique_id}.example.com/posting/101"
        payload = {
            "title": "Data Pipeline Engineer",
            "company": "DataStream Corp",
            "description_text": (
                "Title: Data Pipeline Engineer\n"
                "Company: DataStream Corp\n"
                "Requirements: 3+ years in Python, SQL, Apache Spark, and Kafka streaming pipelines."
            ),
            "source_url": source_url
        }

        # First creation
        resp1 = client.post("/api/v1/jobs/manual", json=payload)
        assert resp1.status_code == 200
        first_id = resp1.json()["id"]

        # Duplicate creation with same canonical source_url
        resp2 = client.post("/api/v1/jobs/manual", json=payload)
        assert resp2.status_code == 200
        second_id = resp2.json()["id"]

        # Deduplication must return the identical record ID
        assert first_id == second_id

    def test_reject_manual_job_too_short(self, client: APITestClient):
        payload = {
            "title": "Engineer",
            "company": "Acme",
            "description_text": "Too short JD"
        }
        response = client.post("/api/v1/jobs/manual", json=payload)
        assert response.status_code == 400
        assert "too short" in response.json()["detail"].lower()

    def test_reject_manual_job_missing_description(self, client: APITestClient):
        payload = {
            "title": "Frontend Engineer",
            "company": "Acme Corp"
        }
        response = client.post("/api/v1/jobs/manual", json=payload)
        assert response.status_code == 422  # Missing required field

    def test_scrape_job_restricted_domain_linkedin(self, client: APITestClient):
        payload = {"url": "https://www.linkedin.com/jobs/view/987654321"}
        response = client.post("/api/v1/jobs/scrape", json=payload)
        assert response.status_code == 403
        data = response.json()
        assert "restricted" in data["detail"].lower()
        assert "linkedin.com" in data["detail"]

    def test_scrape_job_restricted_domain_indeed(self, client: APITestClient):
        payload = {"url": "https://www.indeed.com/viewjob?jk=abcdef123456"}
        response = client.post("/api/v1/jobs/scrape", json=payload)
        assert response.status_code == 403
        data = response.json()
        assert "restricted" in data["detail"].lower()
        assert "indeed.com" in data["detail"]

    def test_scrape_job_malformed_url_422(self, client: APITestClient):
        payload = {"url": "not-a-valid-http-url"}
        response = client.post("/api/v1/jobs/scrape", json=payload)
        # Fast fail: either HTTP 422 from Pydantic or 422 from ScraperError
        assert response.status_code == 422

    def test_list_jobs_with_pagination(self, client: APITestClient, seeded_job: dict):
        response = client.get("/api/v1/jobs?skip=0&limit=5")
        assert response.status_code == 200
        data = response.json()

        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) <= 5
        assert data["total"] >= 1
        assert response.latency_seconds < 2.0

    def test_list_jobs_with_keyword_search(self, client: APITestClient, seeded_job: dict):
        # Search by company name from seeded job
        company_query = seeded_job["company"]
        response = client.get(f"/api/v1/jobs?search={company_query}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any(j["company"] == company_query for j in data["items"])

    def test_get_job_by_id(self, client: APITestClient, seeded_job: dict):
        job_id = seeded_job["id"]
        response = client.get(f"/api/v1/jobs/{job_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == job_id
        assert data["title"] == seeded_job["title"]
        assert data["company"] == seeded_job["company"]

    def test_get_job_not_found_404(self, client: APITestClient):
        response = client.get("/api/v1/jobs/999999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
