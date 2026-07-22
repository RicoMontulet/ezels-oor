"""Recording via `arecord` (ALSA), aimed at a Jabra PHS002W plugged into the Pi."""

import re
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

    def __init__(self, device: str, recordings_dir: Path):
        self._device = device
        self._recordings_dir = recordings_dir
        self._recordings_dir.mkdir(parents=True, exist_ok=True)
        self._process: Optional[subprocess.Popen] = None
        self._path: Optional[Path] = None
        self._started_at: Optional[float] = None
        self._lock = threading.Lock()

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
                    stderr=subprocess.PIPE,
                )
            except FileNotFoundError as exc:
                raise RecorderError("arecord is niet geinstalleerd (alsa-utils)") from exc

            time.sleep(0.2)
            if process.poll() is not None:
                stderr = process.stderr.read().decode(errors="replace").strip()
                raise RecorderError(f"opname kon niet starten: {stderr or 'onbekende fout'}")

            self._process = process
            self._path = path
            self._started_at = time.time()
            return path

    def stop(self) -> tuple[Path, float]:
        with self._lock:
            if self._process is None or self._process.poll() is not None:
                raise RecorderError("er loopt geen opname")

            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait()

            duration = time.time() - self._started_at
            path = self._path
            self._process = None
            self._path = None
            self._started_at = None
            return path, duration
