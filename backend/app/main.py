from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .config import Settings, get_settings
from .repository import Repository
from .schemas import (
    Analysis,
    Problem,
    ProcessingStatus,
    Recording,
    RecordingAccepted,
    RecordingList,
    Summary,
    Transcript,
)

ALLOWED_EXTENSIONS = {".wav", ".flac", ".m4a", ".mp3", ".ogg", ".aac"}


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    repository = Repository(settings)
    repository.initialize()
    app = FastAPI(title="EzelsOor Backend API", version="1.0.0")
    app.state.repository = repository
    app.state.settings = settings

    @app.exception_handler(HTTPException)
    async def problem_response(_: Request, exc: HTTPException):
        if isinstance(exc.detail, Problem):
            detail = exc.detail.model_dump()
        elif isinstance(exc.detail, dict):
            detail = exc.detail
        else:
            detail = {"code": "REQUEST_FAILED", "message": str(exc.detail)}
        return JSONResponse(status_code=exc.status_code, content=detail, media_type="application/problem+json")

    @app.exception_handler(RequestValidationError)
    async def validation_problem(_: Request, __: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=Problem(code="INVALID_UPLOAD", message="The upload metadata or audio file is invalid.").model_dump(),
            media_type="application/problem+json",
        )

    @app.post("/recordings", response_model=RecordingAccepted, status_code=202)
    async def upload_recording(
        audio: UploadFile = File(...),
        title: str | None = Form(default=None),
        recordedAt: datetime | None = Form(default=None),
        locale: str | None = Form(default=None),
    ) -> RecordingAccepted:
        filename = Path(audio.filename or "recording").name
        if title is not None and not 1 <= len(title) <= 200:
            raise HTTPException(422, Problem(code="INVALID_UPLOAD", message="The upload metadata or audio file is invalid."))
        suffix = Path(filename).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise HTTPException(415, Problem(code="UNSUPPORTED_AUDIO_TYPE", message="The uploaded audio format is not supported."))
        recording_id = f"pending-{datetime.now(UTC).timestamp()}"
        upload_dir = settings.storage_path / recording_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        destination = upload_dir / filename
        size = 0
        try:
            with destination.open("wb") as output:
                while chunk := await audio.read(1024 * 1024):
                    size += len(chunk)
                    if size > settings.upload_max_bytes:
                        output.close()
                        destination.unlink(missing_ok=True)
                        raise HTTPException(413, Problem(code="UPLOAD_TOO_LARGE", message="The audio file exceeds the supported upload size."))
                    output.write(chunk)
            if size == 0:
                destination.unlink(missing_ok=True)
                raise HTTPException(422, Problem(code="INVALID_UPLOAD", message="The audio file is empty."))
            recording = repository.create_recording(
                title=title or Path(filename).stem,
                recorded_at=recordedAt or datetime.now(UTC),
                filename=filename,
                content_type=audio.content_type,
                file_path=destination,
                locale=locale or settings.default_locale,
            )
        except Exception as exc:
            if not isinstance(exc, HTTPException):
                destination.unlink(missing_ok=True)
            raise
        finally:
            await audio.close()
        final_dir = settings.storage_path / recording["id"]
        final_dir.mkdir(parents=True, exist_ok=True)
        destination.replace(final_dir / filename)
        repository.update(recording["id"], file_path=str(final_dir / filename))
        return RecordingAccepted(id=recording["id"], status="queued")

    @app.get("/recordings", response_model=RecordingList)
    def list_recordings() -> RecordingList:
        return RecordingList(recordings=[recording_model(row) for row in repository.list_recordings()])

    @app.get("/recordings/{recording_id}/status", response_model=ProcessingStatus)
    def get_status(recording_id: str) -> ProcessingStatus:
        recording = get_recording(repository, recording_id)
        error = None
        if recording["status"] == "failed":
            error = {"code": recording["error_code"], "message": recording["error_message"]}
        return ProcessingStatus(recordingId=recording_id, status=recording["status"], error=error)

    @app.get("/recordings/{recording_id}/transcript", response_model=Transcript)
    def get_transcript(recording_id: str) -> Transcript:
        return result(repository, recording_id, "transcript", Transcript)

    @app.get("/recordings/{recording_id}/summary", response_model=Summary)
    def get_summary(recording_id: str) -> Summary:
        return result(repository, recording_id, "summary", Summary)

    @app.get("/recordings/{recording_id}/analysis", response_model=Analysis)
    def get_analysis(recording_id: str) -> Analysis:
        return result(repository, recording_id, "analysis", Analysis)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


def get_recording(repository: Repository, recording_id: str) -> dict:
    recording = repository.get(recording_id)
    if not recording:
        raise HTTPException(404, Problem(code="RECORDING_NOT_FOUND", message="No recording exists with the supplied identifier."))
    return recording


def recording_model(row: dict) -> Recording:
    return Recording(
        id=row["id"],
        title=row["title"],
        recordedAt=datetime.fromisoformat(row["recorded_at"]),
        filename=row["filename"],
        durationMilliseconds=row["duration_milliseconds"],
        locale=row["locale"],
        status=row["status"],
    )


def result(repository: Repository, recording_id: str, kind: str, model):
    recording = get_recording(repository, recording_id)
    if recording["status"] != "completed":
        raise HTTPException(409, Problem(code="RESULTS_NOT_READY", message="Processing has not completed, so the requested result is not available."))
    value = repository.load_result(recording, kind)
    if value is None:
        raise HTTPException(409, Problem(code="RESULTS_NOT_READY", message="Processing has not completed, so the requested result is not available."))
    return model.model_validate(value)


app = create_app()
