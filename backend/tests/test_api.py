from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def make_client(tmp_path: object) -> TestClient:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path}/ezelsoor.db",
        storage_path=tmp_path / "uploads",
    )
    return TestClient(create_app(settings))


def test_upload_lists_and_reports_queued_status(tmp_path):
    client = make_client(tmp_path)

    response = client.post(
        "/recordings",
        data={"title": "Demo", "recordedAt": "2026-07-13T09:30:00Z", "locale": "en-US"},
        files={"audio": ("demo.flac", b"audio", "audio/flac")},
    )

    assert response.status_code == 202
    recording_id = response.json()["id"]
    assert response.json()["status"] == "queued"
    assert client.get(f"/recordings/{recording_id}/status").json() == {
        "recordingId": recording_id,
        "status": "queued",
        "error": None,
    }
    listed = client.get("/recordings").json()["recordings"]
    assert listed[0]["title"] == "Demo"
    assert listed[0]["filename"] == "demo.flac"
    assert listed[0]["durationMilliseconds"] == 0


def test_upload_rejects_unknown_audio_format(tmp_path):
    client = make_client(tmp_path)

    response = client.post("/recordings", files={"audio": ("notes.txt", b"text", "text/plain")})

    assert response.status_code == 415
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "UNSUPPORTED_AUDIO_TYPE"


def test_upload_validation_uses_problem_response(tmp_path):
    client = make_client(tmp_path)

    response = client.post(
        "/recordings",
        data={"recordedAt": "not-a-date"},
        files={"audio": ("demo.flac", b"audio", "audio/flac")},
    )

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "INVALID_UPLOAD"


def test_result_is_unavailable_until_processing_completes(tmp_path):
    client = make_client(tmp_path)
    created = client.post("/recordings", files={"audio": ("demo.flac", b"audio", "audio/flac")}).json()

    response = client.get(f"/recordings/{created['id']}/transcript")

    assert response.status_code == 409
    assert response.json()["code"] == "RESULTS_NOT_READY"
