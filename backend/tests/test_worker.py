from datetime import UTC, datetime

from app.config import Settings
from app.repository import Repository
from app.services import analysis_from_language, transcript_from_speech
from app.worker import process_one


class FakeAzure:
    def transcribe(self, _audio_path, _locale):
        return {
            "durationMilliseconds": 500,
            "combinedPhrases": [{"text": "Hello world."}],
            "phrases": [
                {
                    "speaker": 1,
                    "offsetMilliseconds": 0,
                    "durationMilliseconds": 500,
                    "text": "Hello world.",
                    "locale": "en-US",
                    "confidence": 0.9,
                }
            ],
        }

    def analyze(self, _transcript, _locale, kind):
        if kind == "SentimentAnalysis":
            return {
                "results": {
                    "documents": [
                        {
                            "sentiment": "neutral",
                            "confidenceScores": {"positive": 0, "neutral": 1, "negative": 0},
                            "sentences": [],
                        }
                    ]
                }
            }
        return {"results": {"documents": [{"keyPhrases": ["world"]}]}}

    def summarize(self, _transcript):
        return {"summary": "Greeting.", "agreements": [], "actionItems": [], "openQuestions": []}


def test_worker_completes_a_sqlite_queued_recording(tmp_path):
    settings = Settings(database_url=f"sqlite:///{tmp_path}/test.db", storage_path=tmp_path / "uploads")
    repository = Repository(settings)
    repository.initialize()
    audio_path = tmp_path / "audio.flac"
    audio_path.write_bytes(b"audio")
    recording = repository.create_recording(
        title="Demo",
        recorded_at=datetime.now(UTC),
        filename="audio.flac",
        content_type="audio/flac",
        file_path=audio_path,
        locale="en-US",
    )

    assert process_one(repository, FakeAzure(), "test-worker")

    completed = repository.get(recording["id"])
    assert completed["status"] == "completed"
    assert completed["duration_milliseconds"] == 500
    assert repository.load_result(completed, "transcript")["text"] == "Hello world."
    assert repository.load_result(completed, "summary")["summary"] == "Greeting."
    assert repository.load_result(completed, "analysis")["keyPhrases"] == ["world"]
