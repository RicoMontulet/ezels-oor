import json
from pathlib import Path

import httpx
from pydantic import ValidationError

from .config import Settings
from .schemas import (
    ActionItem,
    Analysis,
    ConfidenceScores,
    SentenceSentiment,
    Sentiment,
    Summary,
    Transcript,
    TranscriptSegment,
)


class ProcessingFailure(Exception):
    def __init__(self, code: str, message: str, *, retryable: bool = False):
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable


def _endpoint(base: str, path: str) -> str:
    return f"{base.rstrip('/')}{path}"


class AzureClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def transcribe(self, audio_path: Path | str, locale: str) -> dict:
        if not self.settings.speech_endpoint or not self.settings.speech_api_key:
            raise ProcessingFailure("SPEECH_NOT_CONFIGURED", "Speech processing is not configured.")
        audio_path = Path(audio_path)
        definition = {"locales": [locale], "diarization": {"enabled": True, "maxSpeakers": 10}}
        content_type = {
            ".aac": "audio/aac",
            ".flac": "audio/flac",
            ".m4a": "audio/mp4",
            ".mp3": "audio/mpeg",
            ".ogg": "audio/ogg",
            ".wav": "audio/wav",
        }.get(audio_path.suffix.lower(), "application/octet-stream")
        try:
            with audio_path.open("rb") as audio, httpx.Client(timeout=120) as client:
                response = client.post(
                    _endpoint(
                        self.settings.speech_endpoint,
                        f"/speechtotext/transcriptions:transcribe?api-version={self.settings.speech_api_version}",
                    ),
                    headers={"Ocp-Apim-Subscription-Key": self.settings.speech_api_key},
                    files={
                        "definition": (None, json.dumps(definition), "application/json"),
                        "audio": (audio_path.name, audio, content_type),
                    },
                )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise ProcessingFailure("TRANSCRIPTION_FAILED", "The recording could not be transcribed.", retryable=True) from exc

    def analyze(self, transcript: str, locale: str, kind: str) -> dict:
        if not self.settings.language_endpoint or not self.settings.language_api_key:
            raise ProcessingFailure("LANGUAGE_NOT_CONFIGURED", "Language analysis is not configured.")
        language = locale.split("-", 1)[0]
        body = {
            "kind": kind,
            "analysisInput": {"documents": [{"id": "recording", "language": language, "text": transcript}]},
        }
        if kind == "SentimentAnalysis":
            body["parameters"] = {"opinionMining": True}
        try:
            with httpx.Client(timeout=60) as client:
                response = client.post(
                    _endpoint(
                        self.settings.language_endpoint,
                        f"/language/:analyze-text?api-version={self.settings.language_api_version}",
                    ),
                    headers={
                        "Ocp-Apim-Subscription-Key": self.settings.language_api_key,
                        "Content-Type": "application/json",
                    },
                    json=body,
                )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise ProcessingFailure("LANGUAGE_ANALYSIS_FAILED", "The transcript could not be analyzed.", retryable=True) from exc

    def summarize(self, transcript: str) -> dict:
        if not all((self.settings.llm_endpoint, self.settings.llm_api_key, self.settings.llm_model)):
            raise ProcessingFailure("SUMMARY_NOT_CONFIGURED", "Summary processing is not configured.")
        prompt = (
            "Return only a JSON object with keys summary, agreements, actionItems, and openQuestions. "
            "Each actionItems entry must have description and may have assignee. "
            f"Transcript:\n{transcript}"
        )
        try:
            with httpx.Client(timeout=90) as client:
                response = client.post(
                    self.settings.llm_endpoint,
                    headers={"api-key": self.settings.llm_api_key, "Content-Type": "application/json"},
                    json={
                        "model": self.settings.llm_model,
                        "max_tokens": self.settings.llm_max_tokens,
                        "temperature": 0,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
            response.raise_for_status()
            payload = response.json()
            content = payload.get("content", [])
            text = "".join(part.get("text", "") for part in content if part.get("type") == "text")
            return parse_json_object(text)
        except httpx.HTTPError as exc:
            raise ProcessingFailure("SUMMARY_FAILED", "The transcript could not be summarized.", retryable=True) from exc
        except json.JSONDecodeError as exc:
            raise ProcessingFailure("SUMMARY_FAILED", "The transcript could not be summarized.") from exc


def parse_json_object(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            text = "\n".join(lines[1:-1]).strip()
    decoder = json.JSONDecoder()
    for index, character in enumerate(text):
        if character == "{":
            value, _ = decoder.raw_decode(text[index:])
            if isinstance(value, dict):
                return value
            break
    raise json.JSONDecodeError("No JSON object found", text, 0)


def transcript_from_speech(recording_id: str, response: dict) -> Transcript:
    phrases = response.get("phrases", [])
    segments = [
        TranscriptSegment(
            speaker=f"Speaker {phrase.get('speaker', 1)}",
            offsetMilliseconds=phrase.get("offsetMilliseconds", 0),
            durationMilliseconds=phrase.get("durationMilliseconds", 0),
            text=phrase.get("text", ""),
            locale=phrase.get("locale", "und"),
            confidence=phrase.get("confidence", 0),
        )
        for phrase in phrases
    ]
    text = " ".join(item.get("text", "").strip() for item in response.get("combinedPhrases", [])).strip()
    if not text:
        text = " ".join(segment.text.strip() for segment in segments).strip()
    return Transcript(recordingId=recording_id, text=text, segments=segments)


def _scores(value: dict) -> ConfidenceScores:
    scores = value.get("confidenceScores", {})
    return ConfidenceScores(
        positive=scores.get("positive", 0), neutral=scores.get("neutral", 0), negative=scores.get("negative", 0)
    )


def _first_document(response: dict) -> dict:
    results = response.get("results") or {}
    documents = results.get("documents") or []
    if results.get("errors") or not documents:
        raise ProcessingFailure(
            "LANGUAGE_ANALYSIS_FAILED",
            "The transcript could not be analyzed.",
            retryable=True,
        )
    return documents[0]


def analysis_from_language(recording_id: str, sentiment_response: dict, key_phrase_response: dict) -> Analysis:
    sentiment_document = _first_document(sentiment_response)
    key_phrase_document = _first_document(key_phrase_response)
    sentences = [
        SentenceSentiment(
            text=sentence.get("text", ""),
            offset=sentence.get("offset", 0),
            length=sentence.get("length", 0),
            sentiment=sentence.get("sentiment", "neutral"),
            confidenceScores=_scores(sentence),
        )
        for sentence in sentiment_document.get("sentences", [])
    ]
    return Analysis(
        recordingId=recording_id,
        sentiment=Sentiment(
            label=sentiment_document.get("sentiment", "neutral"), confidenceScores=_scores(sentiment_document)
        ),
        sentences=sentences,
        keyPhrases=key_phrase_document.get("keyPhrases", []),
    )


def summary_from_llm(recording_id: str, response: dict) -> Summary:
    try:
        return Summary(
            recordingId=recording_id,
            summary=response.get("summary", ""),
            agreements=response.get("agreements", []),
            actionItems=[ActionItem.model_validate(item) for item in response.get("actionItems", [])],
            openQuestions=response.get("openQuestions", []),
        )
    except ValidationError as exc:
        raise ProcessingFailure(
            "SUMMARY_FAILED",
            "The transcript could not be summarized.",
            retryable=True,
        ) from exc
