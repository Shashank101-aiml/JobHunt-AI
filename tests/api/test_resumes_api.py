import time
from pathlib import Path
import pytest
from tests.api.conftest import APITestClient


@pytest.mark.api
class TestResumesAPI:
    """Candidate resume upload, extraction, activation, and management API endpoints."""

    def test_upload_valid_txt_resume(self, client: APITestClient, sample_txt_resume: Path):
        unique_name = f"api_test_backend_{int(time.time())}.txt"
        with open(sample_txt_resume, "rb") as f:
            response = client.post(
                "/api/v1/resumes?set_active=true",
                files={"file": (unique_name, f, "text/plain")}
            )

        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

        data = response.json()
        assert data["id"] > 0
        assert data["filename"] == unique_name
        assert data["file_type"] == "txt"
        assert data["is_active"] is True
        assert isinstance(data["parsed_skills"], str)
        assert len(data["parsed_skills"]) > 0
        assert "contact_info" in data["structured_profile"]
        assert "experience" in data["structured_profile"]

    def test_upload_valid_docx_resume(self, client: APITestClient, sample_docx_resume: Path):
        unique_name = f"api_test_fullstack_{int(time.time())}.docx"
        with open(sample_docx_resume, "rb") as f:
            response = client.post(
                "/api/v1/resumes?set_active=false",
                files={"file": (unique_name, f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == unique_name
        assert data["file_type"] == "docx"
        assert data["is_active"] is False
        assert "skills" in data["structured_profile"]

    def test_upload_valid_pdf_resume(self, client: APITestClient, sample_pdf_resume: Path):
        unique_name = f"api_test_engineer_{int(time.time())}.pdf"
        with open(sample_pdf_resume, "rb") as f:
            response = client.post(
                "/api/v1/resumes?set_active=false",
                files={"file": (unique_name, f, "application/pdf")}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == unique_name
        assert data["file_type"] == "pdf"
        assert data["file_size_bytes"] > 0

    def test_reject_unsupported_file_extension(self, client: APITestClient, invalid_image_file: Path):
        with open(invalid_image_file, "rb") as f:
            response = client.post(
                "/api/v1/resumes",
                files={"file": ("unsupported_photo.jpg", f, "image/jpeg")}
            )

        assert response.status_code == 400
        data = response.json()
        assert "Unsupported file format" in data["detail"]

    def test_reject_empty_zero_byte_file(self, client: APITestClient, empty_resume: Path):
        with open(empty_resume, "rb") as f:
            response = client.post(
                "/api/v1/resumes",
                files={"file": ("empty_profile.txt", f, "text/plain")}
            )

        assert response.status_code == 400
        data = response.json()
        assert "Uploaded file is empty" in data["detail"]

    def test_reject_missing_file_payload(self, client: APITestClient):
        response = client.post("/api/v1/resumes")
        assert response.status_code == 422  # Unprocessable Entity

    def test_list_resumes(self, client: APITestClient):
        response = client.get("/api/v1/resumes")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

        resumes = response.json()
        assert isinstance(resumes, list)
        assert len(resumes) >= 1
        first = resumes[0]
        assert "id" in first
        assert "filename" in first
        assert "file_type" in first
        assert "structured_profile" in first
        assert "parsed_skills" in first
        assert response.latency_seconds < 2.0, f"List resumes latency too high: {response.latency_seconds}s"

    def test_get_active_resume(self, client: APITestClient):
        response = client.get("/api/v1/resumes/active")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "filename" in data
        assert response.latency_seconds < 1.0

    def test_get_resume_by_id(self, client: APITestClient, active_resume: dict):
        resume_id = active_resume["id"]
        response = client.get(f"/api/v1/resumes/{resume_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == resume_id
        assert data["filename"] == active_resume["filename"]

    def test_get_resume_not_found_404(self, client: APITestClient):
        response = client.get("/api/v1/resumes/999999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_activate_resume_lifecycle(self, client: APITestClient, sample_txt_resume: Path):
        # Upload a secondary resume as inactive
        with open(sample_txt_resume, "rb") as f:
            up_resp = client.post(
                "/api/v1/resumes?set_active=false",
                files={"file": (f"secondary_{int(time.time())}.txt", f, "text/plain")}
            )
        assert up_resp.status_code == 200
        target_id = up_resp.json()["id"]

        # Activate it
        act_resp = client.post(f"/api/v1/resumes/{target_id}/activate")
        assert act_resp.status_code == 200
        act_data = act_resp.json()
        assert act_data["id"] == target_id
        assert act_data["is_active"] is True

        # Verify active endpoint reflects the update
        active_check = client.get("/api/v1/resumes/active")
        assert active_check.status_code == 200
        assert active_check.json()["id"] == target_id

    def test_activate_non_existent_resume_404(self, client: APITestClient):
        response = client.post("/api/v1/resumes/999999/activate")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_resume_and_cleanup(self, client: APITestClient, sample_txt_resume: Path):
        # 1. Upload temporary resume
        with open(sample_txt_resume, "rb") as f:
            up_resp = client.post(
                "/api/v1/resumes?set_active=false",
                files={"file": (f"temp_delete_{int(time.time())}.txt", f, "text/plain")}
            )
        assert up_resp.status_code == 200
        del_id = up_resp.json()["id"]

        # 2. Delete it
        del_resp = client.delete(f"/api/v1/resumes/{del_id}")
        assert del_resp.status_code == 200
        assert del_resp.json()["status"] == "deleted"

        # 3. Confirm 404 on subsequent get
        verify_resp = client.get(f"/api/v1/resumes/{del_id}")
        assert verify_resp.status_code == 404
