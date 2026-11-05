import pytest
from tests.api.conftest import APITestClient


@pytest.mark.api
class TestSecurityAndResilienceAPI:
    """Security boundaries, injection payload resilience, Unicode handling, and input validation."""

    def test_sql_injection_resilience_in_search_query(self, client: APITestClient):
        malicious_search = "' OR '1'='1'; DROP TABLE jobs; --"
        response = client.get(f"/api/v1/jobs?search={malicious_search}")
        # Must return clean HTTP 200 with 0 or matched records; never HTTP 500
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_sql_injection_resilience_in_body_parameters(self, client: APITestClient):
        payload = {
            "title": "Backend Engineer'); DROP TABLE resumes; --",
            "company": "SafeCorp'; DELETE FROM jobs; --",
            "description_text": (
                "Title: SQL Injection Safety Verification Engineer\n"
                "Company: SafeCorp\n"
                "Requirements: Ensure parameterized queries and ORM sanitization are impervious to SQL injection."
            )
        }
        response = client.post("/api/v1/jobs/manual", json=payload)
        assert response.status_code == 200
        data = response.json()
        # Verify text was safely stored as literal text without executing SQL
        assert "'); DROP TABLE resumes; --" in data["title"]

        # Verify tables still exist by doing a successful read
        verify_jobs = client.get("/api/v1/jobs")
        assert verify_jobs.status_code == 200

    def test_xss_script_injection_sanitization(self, client: APITestClient):
        payload = {
            "title": "<script>alert('XSS_VULNERABILITY')</script>",
            "company": "<img src=x onerror=alert('PWNED')>",
            "description_text": (
                "Title: Security Engineer\n"
                "Company: Anti-XSS Labs\n"
                "Requirements: 3+ years experience with Content Security Policies and input validation."
            )
        }
        response = client.post("/api/v1/jobs/manual", json=payload)
        assert response.status_code == 200
        data = response.json()
        # Ensure stored without server-side error
        assert "<script>" in data["title"]

    def test_unicode_and_special_character_resilience(self, client: APITestClient):
        payload = {
            "title": "Ingénieur Logiciel Sénior 🚀 (Full-Stack)",
            "company": "Société Générale & Co. — 東京支社",
            "location": "Zürich / São Paulo / دبي",
            "description_text": (
                "Title: Ingénieur Logiciel Sénior\n"
                "Company: Société Générale\n"
                "Requirements: Maîtrise de Python, FastAPI, Docker, and PostgreSQL. Multilingual support: 日本語, Español, Français."
            )
        }
        response = client.post("/api/v1/jobs/manual", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "🚀" in data["title"]
        assert "東京" in data["company"]
        assert "Zürich" in data["location"]

    def test_malformed_json_body_returns_422(self, client: APITestClient):
        # Send raw invalid JSON string with application/json header
        raw_headers = {"Content-Type": "application/json"}
        response = client.session.post(
            f"{client.base_url}/api/v1/jobs/manual",
            data='{"title": "Broken JSON", "company": ',
            headers=raw_headers
        )
        assert response.status_code == 422

    def test_invalid_http_method_returns_405(self, client: APITestClient):
        # DELETE method on GET-only /health endpoint
        response = client.delete("/health")
        assert response.status_code == 405
