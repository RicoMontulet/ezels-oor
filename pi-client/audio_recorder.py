"""Recording via `arecord` (ALSA), aimed at a Jabra PHS002W plugged into the Pi."""

import re
import signal
import subprocess
import threading
import time
from pathlib import Path
from typing import Optional


class RecorderError(Exception):
    pass


def list_capture_devices() -> list[dict]:
    """Parse `arecord -l` into a list of {card, device, name} dicts."""
    try:
        output = subprocess.run(
            ["arecord", "-l"], capture_output=True, text=True, check=True
        ).stdout
    except FileNotFoundError as exc:
        raise RecorderError("arecord is niet geinstalleerd (alsa-utils)") from exc
    except subprocess.CalledProcessError as exc:
        raise RecorderError(f"kon opnameapparaten niet lezen: {exc}") from exc

    pattern = re.compile(r"^card (\d+): .*?\[(.*?)\].*?device (\d+): .*?\[(.*?)\]")
    devices = []
    for line in output.splitlines():
        match = pattern.match(line)
        if match:
            card, card_name, device, device_name = match.groups()
            devices.append(
                {
                    "card": int(card),
                    "device": int(device),
                    "name": f"{card_name} - {device_name}",
                }
            )
    return devices


def find_device(name_hint: str) -> str:
    """Return an ALSA device string (e.g. plughw:1,0) for the first capture
    device whose name contains name_hint (case-insensitive)."""
    devices = list_capture_devices()
    for dev in devices:
        if name_hint.lower() in dev["name"].lower():
            return f"plughw:{dev['card']},{dev['device']}"
    found = [d["name"] for d in devices]
    raise RecorderError(
        f"geen opnameapparaat gevonden met '{name_hint}' in de naam "
        f"(gevonden: {found or 'geen'})"
    )


class Recorder:
    """Wraps `arecord` so only one recording can run at a time."""

    SAMPLE_RATE = 16000
    CHANNELS = 1
    WAV_HEADER_BYTES = 44

    def __init__(self, device: str, recordings_dir: Path, max_recordings: int = 20):
        self._device = device
        self._recordings_dir = recordings_dir
        self._recordings_dir.mkdir(parents=True, exist_ok=True)
        self._max_recordings = max_recordings
        self._process: Optional[subprocess.Popen] = None
        self._path: Optional[Path] = None
        self._started_at: Optional[float] = None
        self._lock = threading.Lock()
        self._prune_old_recordings()

    def _prune_old_recordings(self) -> None:
        wavs = sorted(self._recordings_dir.glob("recording-*.wav"), key=lambda p: p.stat().st_mtime)
        excess = len(wavs) - self._max_recordings
        for path in wavs[: max(0, excess)]:
            path.unlink(missing_ok=True)

    @property
    def is_recording(self) -> bool:
        with self._lock:
            return self._process is not None and self._process.poll() is None

    def elapsed(self) -> float:
        with self._lock:
            if self._started_at is None:
                return 0.0
            return time.time() - self._started_at

    def start(self) -> Path:
        with self._lock:
            if self._process is not None and self._process.poll() is None:
                raise RecorderError("er loopt al een opname")

            timestamp = time.strftime("%Y%m%dT%H%M%S")
            path = self._recordings_dir / f"recording-{timestamp}.wav"
            try:
                process = subprocess.Popen(
                    [
                        "arecord",
                        "-D", self._device,
                        "-f", "S16_LE",
                        "-r", str(self.SAMPLE_RATE),
                        "-c", str(self.CHANNELS),
                        str(path),
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except FileNotFoundError as exc:
                raise RecorderError("arecord is niet geinstalleerd (alsa-utils)") from exc

            self._process = process
            self._path = path
            self._started_at = time.time()

        time.sleep(0.2)
        with self._lock:
            if self._process is not process:
                raise RecorderError("opname kon niet starten: state changed")
            if process.poll() is not None:
                self._process = None
                self._path = None
                self._started_at = None
                path.unlink(missing_ok=True)
                raise RecorderError("opname kon niet starten: onbekende fout")
            return path

    def stop(self) -> tuple[Path, float]:
        with self._lock:
            if self._process is None or self._process.poll() is not None:
                raise RecorderError("er loopt geen opname")

            process = self._process
            path = self._path
            started_at = self._started_at

        # Wait outside the lock so /api/status is not blocked for seconds.
        # Keep _process set until wait finishes so start() still sees is_recording.
        process.send_signal(signal.SIGINT)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

        with self._lock:
            if self._process is process:
                self._process = None
                self._path = None
                self._started_at = None

            duration = time.time() - started_at

            if path is None or not path.exists() or path.stat().st_size <= self.WAV_HEADER_BYTES:
                if path is not None:
                    path.unlink(missing_ok=True)
                raise RecorderError("opnamebestand is leeg of corrupt")

            self._prune_old_recordings()
            return path, duration
