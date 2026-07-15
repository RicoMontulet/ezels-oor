import json
from pathlib import Path

import httpx

from app.config import Settings
from app.services import AzureClient, analysis_from_language, parse_json_object, transcript_from_speech


def fixture_response() -> dict:
    root = Path(__file__).parents[2]
    with (root / "samples/test-data/api-responses.json").open() as file:
        return json.load(file)


def test_transcript_maps_speaker_segments_from_speech_fixture():
    response = fixture_response()["speechFastTranscription"]["responses"]["multi-speaker-sequence.flac"]

    transcript = transcript_from_speech("rec_test", response)

    assert transcript.recordingId == "rec_test"
    assert len(transcript.segments) == 6
    assert [segment.speaker for segment in transcript.segments] == ["Speaker 1", "Speaker 2", "Speaker 2", "Speaker 2", "Speaker 3", "Speaker 3"]
    assert transcript.segments[1].offsetMilliseconds == 4400
    assert transcript.text.startswith("The Delawares are children")


def test_analysis_maps_language_fixture():
    fixture = fixture_response()["language"]

    analysis = analysis_from_language(
        "rec_test", fixture["sentimentAnalysis"], fixture["keyPhraseExtraction"]
    )

    assert analysis.sentiment.label == "negative"
    assert analysis.sentences[3].offset == 123
    assert "stone walls" in analysis.keyPhrases


def test_speech_client_accepts_repository_string_path_and_uses_audio_mime_type(tmp_path, monkeypatch):
    audio = tmp_path / "fixture.flac"
    audio.write_bytes(b"audio")
    captured = {}

    def post(self, _url, **kwargs):
        captured["content_type"] = kwargs["files"]["audio"][2]
        return httpx.Response(200, json={}, request=httpx.Request("POST", _url))

    monkeypatch.setattr(httpx.Client, "post", post)
    client = AzureClient(Settings(speech_endpoint="https://speech.example", speech_api_key="key"))

    client.transcribe(str(audio), "en-US")

    assert captured["content_type"] == "audio/flac"


def test_summary_parser_accepts_a_fenced_json_response():
    response = parse_json_object(
        "```json\n{\"summary\": \"Done\", \"agreements\": [], \"actionItems\": [], \"openQuestions\": []}\n```"
    )

    assert response["summary"] == "Done"
