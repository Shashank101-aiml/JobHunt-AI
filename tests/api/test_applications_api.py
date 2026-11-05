import time
import pytest
from tests.api.conftest import APITestClient


@pytest.mark.api
class TestApplicationsAPI:
    """Application pipeline trigger, review, lifecycle updates, submission, events, and DOCX export."""

    @pytest.fixture
    def fresh_application(self, client: APITestClient, active_resume: dict) -> dict:
        unique_id = int(time.time() * 1000)
        payload = {
            "resume_id": active_resume["id"],
            "job_text": (
                f"Title: Principal Cloud Infrastructure Engineer {unique_id}\n"
                f"Company: HyperScale Dynamics {unique_id}\n"
                "Requirements:\n"
                "- 6+ years production Python and Linux system administration\n"
                "- Advanced Docker containerization and Kubernetes orchestration\n"
                "- Relational databases: PostgreSQL performance tuning and migrations"
            )
        }
        resp = client.post("/api/v1/apply?sync_execution=true", json=payload)
        assert resp.status_code == 200, f"Failed to create fresh application: {resp.text}"
        return resp.json()

    def test_trigger_application_sync_execution(self, fresh_application: dict):
        assert fresh_application["id"] > 0
        assert fresh_application["status"] == "ready_for_review"
        assert fresh_application["ats_score"] is not None
        assert 0 <= fresh_application["ats_score"] <= 100
        assert fresh_application["tailored_resume_text"] is not None
        assert len(fresh_application["tailored_resume_text"]) > 50
        assert fresh_application["cover_letter"] is not None
        assert len(fresh_application["cover_letter"]) > 50

    def test_application_duplicate_prevention(
        self,
        client: APITestClient,
        active_resume: dict,
        seeded_job: dict
    ):
        payload = {
            "resume_id": active_resume["id"],
            "job_id": seeded_job["id"]
        }

        # First trigger
        resp1 = client.post("/api/v1/apply?sync_execution=true", json=payload)
        assert resp1.status_code == 200
        app1_id = resp1.json()["id"]

        # Duplicate trigger with exact same resume and job
        resp2 = client.post("/api/v1/apply?sync_execution=true", json=payload)
        assert resp2.status_code == 200
        app2_id = resp2.json()["id"]

        assert app1_id == app2_id

    def test_list_applications_and_filtering(self, client: APITestClient, fresh_application: dict):
        response = client.get("/api/v1/applications?status=ready_for_review&limit=10")
        assert response.status_code == 200
        data = response.json()

        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)
        assert any(app["id"] == fresh_application["id"] for app in data["items"])

    def test_get_application_by_id(self, client: APITestClient, fresh_application: dict):
        app_id = fresh_application["id"]
        response = client.get(f"/api/v1/applications/{app_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == app_id
        assert data["status"] == fresh_application["status"]
        assert data["tailored_resume_text"] == fresh_application["tailored_resume_text"]

    def test_get_application_status_lightweight(self, client: APITestClient, fresh_application: dict):
        app_id = fresh_application["id"]
        response = client.get(f"/api/v1/status/{app_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == app_id
        assert "status" in data
        assert "ats_score" in data
        assert response.latency_seconds < 1.0

    def test_get_application_not_found_404(self, client: APITestClient):
        response = client.get("/api/v1/applications/999999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_save_application_review_edits(self, client: APITestClient, fresh_application: dict):
        app_id = fresh_application["id"]
        updated_resume = "Alex Rivera - Principal Cloud Infrastructure Engineer\n\nCustomized bullet points."
        updated_cover = "Dear HyperScale Dynamics Team,\n\nI am writing to express my enthusiasm."
        candidate_notes = "Spoke with recruiter on LinkedIn; screening scheduled."

        review_payload = {
            "tailored_resume_text": updated_resume,
            "cover_letter": updated_cover,
            "notes": candidate_notes
        }
        response = client.post(f"/api/v1/applications/{app_id}/review", json=review_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["tailored_resume_text"] == updated_resume
        assert data["cover_letter"] == updated_cover
        assert data["notes"] == candidate_notes

        # Verify audit trail recorded the edit event
        events_resp = client.get(f"/api/v1/applications/{app_id}/events")
        assert events_resp.status_code == 200
        event_types = [e["event_type"] for e in events_resp.json()]
        assert "review_updated" in event_types

    def test_patch_application_status_lifecycle(self, client: APITestClient, fresh_application: dict):
        app_id = fresh_application["id"]

        # Transition to interviewing
        patch_resp = client.patch(f"/api/v1/applications/{app_id}?status=interviewing&notes=First%20round%20passed")
        assert patch_resp.status_code == 200
        data = patch_resp.json()
        assert data["status"] == "interviewing"
        assert data["notes"] == "First round passed"

        # Verify invalid status is rejected with HTTP 400
        invalid_resp = client.patch(f"/api/v1/applications/{app_id}?status=invalid_status_xyz")
        assert invalid_resp.status_code == 400
        assert "invalid status" in invalid_resp.json()["detail"].lower()

    def test_submit_application_without_confirmation(self, client: APITestClient, fresh_application: dict):
        app_id = fresh_application["id"]
        submit_payload = {
            "submission_type": "manual",
            "candidate_confirmed": False,
            "notes": "Package prepared; portal submission pending."
        }
        response = client.post(f"/api/v1/applications/{app_id}/submit", json=submit_payload)
        assert response.status_code == 200
        data = response.json()
        # Unconfirmed manual submission requires candidate action
        assert data["status"] == "requires_manual_action"
        assert data["submission_type"] == "manual"

    def test_submit_application_with_confirmation(self, client: APITestClient, fresh_application: dict):
        app_id = fresh_application["id"]
        submit_payload = {
            "submission_type": "manual",
            "candidate_confirmed": True,
            "notes": "Candidate manually submitted via employer portal and confirmed."
        }
        response = client.post(f"/api/v1/applications/{app_id}/submit", json=submit_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "submitted"
        assert data["submitted_at"] is not None

    def test_get_application_audit_events(self, client: APITestClient, fresh_application: dict):
        app_id = fresh_application["id"]
        response = client.get(f"/api/v1/applications/{app_id}/events")
        assert response.status_code == 200
        events = response.json()
        assert isinstance(events, list)
        assert len(events) >= 1
        first_event = events[0]
        assert "id" in first_event
        assert "event_type" in first_event
        assert "message" in first_event
        assert "created_at" in first_event

    def test_download_tailored_docx_endpoint(self, client: APITestClient, fresh_application: dict):
        app_id = fresh_application["id"]
        response = client.get(f"/api/v1/applications/{app_id}/download-docx")
        assert response.status_code == 200

        # Header assertions
        content_type = response.headers.get("content-type", "")
        assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in content_type

        content_disp = response.headers.get("content-disposition", "")
        assert f"tailored_resume_app_{app_id}.docx" in content_disp

        # Binary integrity assertion (> 1KB valid DOCX)
        file_bytes = response.content
        assert len(file_bytes) > 1000, f"DOCX file size suspiciously small: {len(file_bytes)} bytes"
        # Standard ZIP magic header for DOCX documents (PK\x03\x04)
        assert file_bytes[:4] == b"PK\x03\x04", "File does not have valid DOCX / OOXML magic header"

    def test_download_docx_not_found_404(self, client: APITestClient):
        response = client.get("/api/v1/applications/999999/download-docx")
        assert response.status_code == 404
