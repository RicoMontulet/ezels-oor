from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

RecordingStatus = Literal["queued", "transcribing", "analyzing", "completed", "failed"]
SentimentLabel = Literal["positive", "neutral", "negative", "mixed"]


class Problem(BaseModel):
    code: str
    message: str


class RecordingAccepted(BaseModel):
    id: str
    status: RecordingStatus


class Recording(BaseModel):
    id: str
    title: str
    recordedAt: datetime
    filename: str
    durationMilliseconds: int = Field(ge=0)
    locale: str
    status: RecordingStatus


class RecordingList(BaseModel):
    recordings: list[Recording]


class ProcessingError(BaseModel):
    code: str
    message: str


class ProcessingStatus(BaseModel):
    recordingId: str
    status: RecordingStatus
    error: ProcessingError | None = None


class TranscriptSegment(BaseModel):
    speaker: str
    offsetMilliseconds: int = Field(ge=0)
    durationMilliseconds: int = Field(ge=0)
    text: str
    locale: str
    confidence: float = Field(ge=0, le=1)


class Transcript(BaseModel):
    recordingId: str
    text: str
    segments: list[TranscriptSegment]


class ActionItem(BaseModel):
    description: str
    assignee: str | None = None


class Summary(BaseModel):
    recordingId: str
    summary: str
    agreements: list[str]
    actionItems: list[ActionItem]
    openQuestions: list[str]


class ConfidenceScores(BaseModel):
    positive: float = Field(ge=0, le=1)
    neutral: float = Field(ge=0, le=1)
    negative: float = Field(ge=0, le=1)


class Sentiment(BaseModel):
    label: SentimentLabel
    confidenceScores: ConfidenceScores


class SentenceSentiment(BaseModel):
    text: str
    offset: int = Field(ge=0)
    length: int = Field(ge=0)
    sentiment: SentimentLabel
    confidenceScores: ConfidenceScores


class Analysis(BaseModel):
    recordingId: str
    sentiment: Sentiment
    sentences: list[SentenceSentiment]
    keyPhrases: list[str]
