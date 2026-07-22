import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from .config import Settings


def utcnow() -> datetime:
    return datetime.now(UTC)


def timestamp(value: datetime | None = None) -> str:
    return (value or utcnow()).isoformat()


class Repository:
    def __init__(self, settings: Settings):
        if not settings.database_url.startswith("sqlite:///"):
            raise ValueError("Only sqlite database URLs are supported")
        self.database_path = Path(settings.database_url.removeprefix("sqlite:///"))
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings = settings

    @contextmanager
    def connection(self):
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS recordings (
                  id TEXT PRIMARY KEY,
                  title TEXT NOT NULL,
                  recorded_at TEXT NOT NULL,
                  filename TEXT NOT NULL,
                  content_type TEXT,
                  file_path TEXT NOT NULL,
                  duration_milliseconds INTEGER NOT NULL DEFAULT 0,
                  locale TEXT NOT NULL,
                  status TEXT NOT NULL,
                  attempts INTEGER NOT NULL DEFAULT 0,
                  next_attempt_at TEXT,
                  claimed_at TEXT,
                  worker_id TEXT,
                  error_code TEXT,
                  error_message TEXT,
                  transcript_json TEXT,
                  summary_json TEXT,
                  analysis_json TEXT,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                )
                """
            )

    def create_recording(
        self,
        *,
        title: str,
        recorded_at: datetime,
        filename: str,
        content_type: str | None,
        file_path: Path,
        locale: str,
        recording_id: str | None = None,
    ) -> dict:
        recording_id = recording_id or f"rec_{uuid4().hex}"
        now = timestamp()
        row = {
            "id": recording_id,
            "title": title,
            "recorded_at": timestamp(recorded_at),
            "filename": filename,
            "content_type": content_type,
            "file_path": str(file_path),
            "duration_milliseconds": 0,
            "locale": locale,
            "status": "queued",
            "created_at": now,
            "updated_at": now,
        }
        with self.connection() as connection:
            connection.execute(
                """INSERT INTO recordings (
                  id, title, recorded_at, filename, content_type, file_path,
                  duration_milliseconds, locale, status, created_at, updated_at
                ) VALUES (
                  :id, :title, :recorded_at, :filename, :content_type, :file_path,
                  :duration_milliseconds, :locale, :status, :created_at, :updated_at
                )""",
                row,
            )
        return row

    def list_recordings(self) -> list[dict]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM recordings ORDER BY recorded_at DESC, created_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def get(self, recording_id: str) -> dict | None:
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM recordings WHERE id = ?", (recording_id,)).fetchone()
        return dict(row) if row else None

    def claim_next(self, worker_id: str) -> dict | None:
        now = utcnow()
        stale_before = timestamp(now - timedelta(seconds=self.settings.worker_lease_seconds))
        with self.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """UPDATE recordings
                   SET status = 'queued', claimed_at = NULL, worker_id = NULL,
                       updated_at = ?
                   WHERE status IN ('transcribing', 'analyzing') AND claimed_at < ?""",
                (timestamp(now), stale_before),
            )
            row = connection.execute(
                """SELECT * FROM recordings
                   WHERE status = 'queued'
                     AND attempts < ?
                     AND (next_attempt_at IS NULL OR next_attempt_at <= ?)
                   ORDER BY created_at
                   LIMIT 1""",
                (self.settings.max_processing_attempts, timestamp(now)),
            ).fetchone()
            if row is None:
                return None
            # Resume at last unfinished phase when transcript already stored.
            phase = "analyzing" if row["transcript_json"] else "transcribing"
            connection.execute(
                """UPDATE recordings
                   SET status = ?, attempts = attempts + 1,
                       claimed_at = ?, worker_id = ?, error_code = NULL,
                       error_message = NULL, updated_at = ?
                   WHERE id = ?""",
                (phase, timestamp(now), worker_id, timestamp(now), row["id"]),
            )
            claimed = connection.execute("SELECT * FROM recordings WHERE id = ?", (row["id"],)).fetchone()
        return dict(claimed)

    def update(self, recording_id: str, **values) -> None:
        if not values:
            return
        values["updated_at"] = timestamp()
        assignments = ", ".join(f"{column} = :{column}" for column in values)
        values["id"] = recording_id
        with self.connection() as connection:
            connection.execute(f"UPDATE recordings SET {assignments} WHERE id = :id", values)

    def store_result(self, recording_id: str, kind: str, value: dict) -> None:
        if kind not in {"transcript", "summary", "analysis"}:
            raise ValueError(f"Unknown result kind: {kind}")
        self.update(recording_id, **{f"{kind}_json": json.dumps(value)})

    def load_result(self, recording: dict, kind: str) -> dict | None:
        raw = recording[f"{kind}_json"]
        return json.loads(raw) if raw else None
