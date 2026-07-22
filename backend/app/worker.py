import argparse
import json
import logging
import socket
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

from .config import get_settings
from .repository import Repository
from .schemas import Analysis, Summary, Transcript
from .services import (
    AzureClient,
    ProcessingFailure,
    analysis_from_language,
    summary_from_llm,
    transcript_from_speech,
)

logger = logging.getLogger(__name__)


def _schedule_retry(repository: Repository, recording: dict, code: str, message: str) -> None:
    recording_id = recording["id"]
    attempts = recording["attempts"]
    if attempts < repository.settings.max_processing_attempts:
        repository.update(
            recording_id,
            status="queued",
            claimed_at=None,
            worker_id=None,
            next_attempt_at=(
                datetime.now(UTC) + timedelta(seconds=repository.settings.retry_delay_seconds)
            ).isoformat(),
            error_code=code,
            error_message=message,
        )
        logger.warning("Processing %s will retry after failure: %s", recording_id, code)
    else:
        repository.update(
            recording_id,
            status="failed",
            claimed_at=None,
            worker_id=None,
            error_code=code,
            error_message=message,
        )
        logger.warning("Processing %s failed: %s", recording_id, code)


def process_one(repository: Repository, azure: AzureClient, worker_id: str) -> bool:
    recording = repository.claim_next(worker_id)
    if not recording:
        return False
    recording_id = recording["id"]
    try:
        if recording.get("transcript_json"):
            transcript = Transcript.model_validate(json.loads(recording["transcript_json"]))
        else:
            audio_path = Path(recording["file_path"])
            if not audio_path.is_file():
                raise ProcessingFailure(
                    "PROCESSING_FAILED",
                    "The recording audio file is missing.",
                    retryable=True,
                )
            speech = azure.transcribe(audio_path, recording["locale"])
            transcript = transcript_from_speech(recording_id, speech)
            repository.store_result(recording_id, "transcript", transcript.model_dump(mode="json"))
            repository.update(
                recording_id,
                duration_milliseconds=speech.get("durationMilliseconds", 0),
                status="analyzing",
            )

        if recording.get("analysis_json"):
            analysis = Analysis.model_validate(json.loads(recording["analysis_json"]))
        else:
            repository.update(recording_id, status="analyzing")
            # Use detected locale from transcript if original was "auto"
            detected_locale = recording["locale"]
            if detected_locale == "auto" and transcript.segments:
                detected_locale = transcript.segments[0].locale or "en-US"
            sentiment = azure.analyze(transcript.text, detected_locale, "SentimentAnalysis")
            key_phrases = azure.analyze(transcript.text, detected_locale, "KeyPhraseExtraction")
            analysis = analysis_from_language(recording_id, sentiment, key_phrases)
            repository.store_result(recording_id, "analysis", analysis.model_dump(mode="json"))

        if recording.get("summary_json"):
            Summary.model_validate(json.loads(recording["summary_json"]))
        else:
            summary = summary_from_llm(recording_id, azure.summarize(transcript.text))
            repository.store_result(recording_id, "summary", summary.model_dump(mode="json"))

        repository.update(recording_id, status="completed", claimed_at=None, worker_id=None)
    except ProcessingFailure as exc:
        if exc.retryable:
            _schedule_retry(repository, recording, exc.code, exc.message)
        else:
            repository.update(
                recording_id,
                status="failed",
                claimed_at=None,
                worker_id=None,
                error_code=exc.code,
                error_message=exc.message,
            )
            logger.warning("Processing %s failed: %s", recording_id, exc.code)
    except Exception:
        logger.exception("Unexpected failure processing %s", recording_id)
        _schedule_retry(
            repository,
            recording,
            "PROCESSING_FAILED",
            "The recording could not be processed.",
        )
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the EzelsOor processing worker")
    parser.add_argument("--once", action="store_true", help="Process at most one queued recording")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    repository = Repository(settings)
    repository.initialize()
    azure = AzureClient(settings)
    worker_id = socket.gethostname()
    while True:
        processed = process_one(repository, azure, worker_id)
        if args.once:
            return
        if not processed:
            time.sleep(settings.worker_poll_seconds)


if __name__ == "__main__":
    main()
