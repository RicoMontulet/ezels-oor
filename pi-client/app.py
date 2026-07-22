import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests
from audio_recorder import Recorder, RecorderError, find_device
from dotenv import load_dotenv
from flask import Flask, abort, jsonify, render_template, request, send_from_directory

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

RECORDINGS_DIR = Path(os.environ.get("RECORDINGS_DIR", BASE_DIR / "recordings"))
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8082/recordings").strip()
AUDIO_DEVICE_HINT = os.environ.get("AUDIO_DEVICE_HINT", "Jabra")
AUDIO_DEVICE = os.environ.get("AUDIO_DEVICE")  # e.g. plughw:1,0 — skips autodetect
MAX_RECORDINGS = int(os.environ.get("MAX_RECORDINGS", "20"))

app = Flask(__name__)

_state_lock = threading.Lock()
_recorder: Optional[Recorder] = None
_last_recording: Optional[dict] = None
_last_error: Optional[str] = None


def get_recorder() -> Recorder:
    """Lazily build the Recorder so a missing device only errors on use."""
    global _recorder
    with _state_lock:
        if _recorder is None:
            device = AUDIO_DEVICE or find_device(AUDIO_DEVICE_HINT)
            _recorder = Recorder(device=device, recordings_dir=RECORDINGS_DIR, max_recordings=MAX_RECORDINGS)
        return _recorder


def reset_recorder() -> None:
    global _recorder
    with _state_lock:
        _recorder = None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def status():
    device_error = None
    recording = False
    elapsed = 0.0
    try:
        rec = get_recorder()
        recording = rec.is_recording
        elapsed = rec.elapsed()
    except RecorderError as exc:
        device_error = str(exc)

    with _state_lock:
        last = _last_recording
        last_error = _last_error

    return jsonify(
        {
            "recording": recording,
            "elapsed": elapsed,
            "has_recording": last is not None,
            "last_recording": last["name"] if last else None,
            "backend_configured": bool(BACKEND_URL),
            "device_error": device_error,
            "last_error": last_error,
        }
    )


@app.route("/api/record/start", methods=["POST"])
def record_start():
    global _last_error, _last_recording
    try:
        rec = get_recorder()
        rec.start()
        with _state_lock:
            _last_recording = None
            _last_error = None
        return jsonify({"ok": True})
    except RecorderError as exc:
        reset_recorder()
        with _state_lock:
            _last_error = str(exc)
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.route("/api/record/stop", methods=["POST"])
def record_stop():
    global _last_error, _last_recording
    try:
        rec = get_recorder()
        path, duration = rec.stop()
        with _state_lock:
            _last_recording = {
                "path": path,
                "name": path.name,
                "duration_seconds": duration,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
            }
            _last_error = None
            last = _last_recording
        return jsonify({"ok": True, "file": last["name"], "duration": round(duration, 1)})
    except RecorderError as exc:
        with _state_lock:
            _last_error = str(exc)
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.route("/api/recording/file")
def recording_file():
    """Serve the last recording for playback (`<audio>`) or download.

    Pass `?download=1` to force a Content-Disposition attachment.
    Optional `?name=` must match the basename of the last recording.
    """
    with _state_lock:
        last = _last_recording
    if last is None or not last["path"].exists():
        abort(404)

    requested = request.args.get("name")
    if requested is not None:
        safe_name = Path(requested).name
        if safe_name != last["path"].name:
            abort(404)

    as_attachment = request.args.get("download") == "1"
    return send_from_directory(
        RECORDINGS_DIR,
        last["path"].name,
        mimetype="audio/wav",
        as_attachment=as_attachment,
        download_name=last["path"].name,
    )


@app.route("/api/record/send", methods=["POST"])
def record_send():
    global _last_error, _last_recording
    with _state_lock:
        last = _last_recording
    if last is None or not last["path"].exists():
        error = "geen opname beschikbaar om te versturen"
        with _state_lock:
            _last_error = error
        return jsonify({"ok": False, "error": error}), 400
    if not BACKEND_URL:
        error = "BACKEND_URL is niet geconfigureerd"
        with _state_lock:
            _last_error = error
        return jsonify({"ok": False, "error": error}), 400

    path = last["path"]
    try:
        with open(path, "rb") as audio_file:
            response = requests.post(
                BACKEND_URL,
                files={"audio": (path.name, audio_file, "audio/wav")},
                data={
                    "recordedAt": last["recorded_at"],
                    "title": Path(last["name"]).stem or "recording",
                },
                timeout=30,
            )
        response.raise_for_status()
        path.unlink(missing_ok=True)
        with _state_lock:
            _last_error = None
            if _last_recording and _last_recording["path"] == path:
                _last_recording = None
        return jsonify({"ok": True, "backend_status": response.status_code})
    except requests.exceptions.ConnectionError:
        error = f"kan geen verbinding maken met de backend ({BACKEND_URL})"
        with _state_lock:
            _last_error = error
        return jsonify({"ok": False, "error": error}), 502
    except requests.exceptions.Timeout:
        error = "versturen naar de backend duurde te lang (timeout)"
        with _state_lock:
            _last_error = error
        return jsonify({"ok": False, "error": error}), 502
    except requests.exceptions.HTTPError:
        error = f"backend gaf een foutstatus terug: {response.status_code}"
        with _state_lock:
            _last_error = error
        return jsonify({"ok": False, "error": error}), 502
    except requests.RequestException as exc:
        error = f"versturen mislukt: {exc}"
        with _state_lock:
            _last_error = error
        return jsonify({"ok": False, "error": error}), 502


if __name__ == "__main__":
    app.run(
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", 5001)),
        threaded=True,
    )
