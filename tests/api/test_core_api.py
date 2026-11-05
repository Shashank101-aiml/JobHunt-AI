import pytest
from tests.api.conftest import APITestClient


@pytest.mark.api
class TestCoreAPI:
    """Core health check and service infrastructure verification."""

    def test_health_check_status_and_keys(self, client: APITestClient):
        response = client.get("/health")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "job-hunt-api"
        assert "version" in data
        assert data["database"] == "ok"
        assert "vector_store" in data
        assert "llm_provider" in data
        assert "email_service" in data

    def test_health_check_response_latency(self, client: APITestClient):
        response = client.get("/health")
        assert response.status_code == 200
        # Fast endpoint should respond within 500 milliseconds
        assert response.latency_seconds < 0.50, f"Health check exceeded latency budget: {response.latency_seconds}s"

    def test_cors_headers_handling(self, client: APITestClient):
        headers = {
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET"
        }
        response = client.get("/health", headers=headers)
        assert response.status_code == 200
        # Verify CORS allow origin header is surfaced
        assert response.headers.get("access-control-allow-origin") in ["http://localhost:5173", "*"]

    def test_dashboard_stats_endpoint(self, client: APITestClient):
        response = client.get("/api/v1/dashboard/stats")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

        data = response.json()
        required_keys = [
            "total_jobs",
            "total_applications",
            "awaiting_review",
            "submitted",
            "interviewing",
            "status_distribution"
        ]
        for key in required_keys:
            assert key in data, f"Missing key in dashboard stats: {key}"

        assert isinstance(data["total_jobs"], int)
        assert isinstance(data["total_applications"], int)
        assert isinstance(data["status_distribution"], dict)
        assert response.latency_seconds < 2.0, f"Dashboard stats latency too high: {response.latency_seconds}s"
