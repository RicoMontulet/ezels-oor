import argparse
import logging
import socket
import time
from datetime import UTC, datetime, timedelta

from .config import get_settings
from .repository import Repository
from .services import (
    AzureClient,
    ProcessingFailure,
    analysis_from_language,
    summary_from_llm,
    transcript_from_speech,
)

logger = logging.getLogger(__name__)


def process_one(repository: Repository, azure: AzureClient, worker_id: str) -> bool:
    recording = repository.claim_next(worker_id)
    if not recording:
        return False
    recording_id = recording["id"]
    try:
        speech = azure.transcribe(recording["file_path"], recording["locale"])
        transcript = transcript_from_speech(recording_id, speech)
        repository.store_result(recording_id, "transcript", transcript.model_dump(mode="json"))
        repository.update(
            recording_id,
            duration_milliseconds=speech.get("durationMilliseconds", 0),
            status="analyzing",
        )

        sentiment = azure.analyze(transcript.text, recording["locale"], "SentimentAnalysis")
        key_phrases = azure.analyze(transcript.text, recording["locale"], "KeyPhraseExtraction")
        analysis = analysis_from_language(recording_id, sentiment, key_phrases)
        repository.store_result(recording_id, "analysis", analysis.model_dump(mode="json"))

        summary = summary_from_llm(recording_id, azure.summarize(transcript.text))
        repository.store_result(recording_id, "summary", summary.model_dump(mode="json"))
        repository.update(recording_id, status="completed", claimed_at=None, worker_id=None)
    except ProcessingFailure as exc:
        attempts = recording["attempts"]
        if exc.retryable and attempts < repository.settings.max_processing_attempts:
            repository.update(
                recording_id,
                status="queued",
                claimed_at=None,
                worker_id=None,
                next_attempt_at=(datetime.now(UTC) + timedelta(seconds=repository.settings.retry_delay_seconds)).isoformat(),
                error_code=exc.code,
                error_message=exc.message,
            )
            logger.warning("Processing %s will retry after failure: %s", recording_id, exc.code)
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
        repository.update(
            recording_id,
            status="failed",
            claimed_at=None,
            worker_id=None,
            error_code="PROCESSING_FAILED",
            error_message="The recording could not be processed.",
        )
        logger.exception("Unexpected failure processing %s", recording_id)
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
