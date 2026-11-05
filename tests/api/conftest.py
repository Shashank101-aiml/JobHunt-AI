import os
import time
from pathlib import Path
from typing import Dict, Any, Generator
import pytest
import requests

DEFAULT_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES_DIR = PROJECT_ROOT / "frontend" / "e2e" / "fixtures" / "test_resumes"


class APITestClient:
    """Wrapper around requests.Session providing base URL resolution and timing metrics."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "JobHunt-API-TestSuite/2.0",
        })

    def request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        kwargs.setdefault("timeout", 20.0)
        start_time = time.perf_counter()
        response = self.session.request(method, url, **kwargs)
        duration = time.perf_counter() - start_time
        # Attach custom latency attribute for performance assertions
        response.latency_seconds = duration
        return response

    def get(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request("GET", endpoint, **kwargs)

    def post(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request("POST", endpoint, **kwargs)

    def patch(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request("PATCH", endpoint, **kwargs)

    def put(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request("PUT", endpoint, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request("DELETE", endpoint, **kwargs)


@pytest.fixture(scope="session")
def base_url() -> str:
    return DEFAULT_BASE_URL


@pytest.fixture(scope="session")
def client(base_url: str) -> APITestClient:
    api_client = APITestClient(base_url)
    # Verify server is online before running API suite
    try:
        resp = api_client.get("/health", timeout=5.0)
        assert resp.status_code == 200, f"Backend returned unexpected status {resp.status_code} at /health"
    except Exception as exc:
        pytest.fail(f"FastAPI backend server is not reachable at {base_url}. Ensure uvicorn is running: {exc}")
    return api_client


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture(scope="session")
def sample_txt_resume(fixtures_dir: Path) -> Path:
    path = fixtures_dir / "sample_backend_resume.txt"
    assert path.exists(), f"Missing fixture: {path}"
    return path


@pytest.fixture(scope="session")
def sample_docx_resume(fixtures_dir: Path) -> Path:
    path = fixtures_dir / "sample_fullstack_resume.docx"
    assert path.exists(), f"Missing fixture: {path}"
    return path


@pytest.fixture(scope="session")
def sample_pdf_resume(fixtures_dir: Path) -> Path:
    path = fixtures_dir / "sample_resume.pdf"
    assert path.exists(), f"Missing fixture: {path}"
    return path


@pytest.fixture(scope="session")
def empty_resume(fixtures_dir: Path) -> Path:
    path = fixtures_dir / "empty_resume.txt"
    assert path.exists(), f"Missing fixture: {path}"
    return path


@pytest.fixture(scope="session")
def invalid_image_file(fixtures_dir: Path) -> Path:
    path = fixtures_dir / "invalid_file.jpg"
    assert path.exists(), f"Missing fixture: {path}"
    return path


@pytest.fixture(scope="session")
def active_resume(client: APITestClient, sample_txt_resume: Path) -> Dict[str, Any]:
    """Ensures an active resume exists on the server and returns its metadata."""
    resp = client.get("/api/v1/resumes/active")
    if resp.status_code == 200:
        return resp.json()

    # Upload a fresh resume if none is active
    with open(sample_txt_resume, "rb") as f:
        up_resp = client.post(
            "/api/v1/resumes?set_active=true",
            files={"file": (f"active_fixture_{int(time.time())}.txt", f, "text/plain")}
        )
    assert up_resp.status_code == 200, f"Failed to upload active resume fixture: {up_resp.text}"
    return up_resp.json()


@pytest.fixture(scope="session")
def seeded_job(client: APITestClient) -> Dict[str, Any]:
    """Creates a seeded manual job for downstream ATS and application tests."""
    unique_id = int(time.time() * 1000)
    payload = {
        "title": f"Senior Distributed Systems Engineer {unique_id}",
        "company": f"AeroCloud Labs {unique_id}",
        "location": "Remote / San Francisco",
        "employment_type": "Full-Time",
        "description_text": (
            "Title: Senior Distributed Systems Engineer\n"
            f"Company: AeroCloud Labs {unique_id}\n"
            "Requirements:\n"
            "- 5+ years building distributed backend services in Python and FastAPI\n"
            "- Strong expertise in PostgreSQL schema design, indexing, and connection pooling\n"
            "- Docker containerization, Kubernetes orchestration, and CI/CD automation\n"
            "- Experience with asynchronous task workers and Redis message queues\n"
            "Preferred Qualifications:\n"
            "- Experience with ChromaDB or vector similarity retrieval systems\n"
            "- Experience building LLM tool-calling or LangGraph agent workflows\n"
            "Responsibilities:\n"
            "- Design and deliver high-throughput RESTful and asynchronous APIs\n"
            "- Optimize application performance and database query latencies"
        ),
        "source_url": f"https://aerocloud-{unique_id}.example.com/careers/404"
    }
    resp = client.post("/api/v1/jobs/manual", json=payload)
    assert resp.status_code == 200, f"Failed to seed job fixture: {resp.text}"
    return resp.json()
