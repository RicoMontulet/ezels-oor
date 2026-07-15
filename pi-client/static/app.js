const btnRecord = document.getElementById("btn-record");
const btnStop = document.getElementById("btn-stop");
const btnSend = document.getElementById("btn-send");
const statusEl = document.getElementById("status");
const timerEl = document.getElementById("timer");
const messageEl = document.getElementById("message");
const playbackEl = document.getElementById("playback");
const playerEl = document.getElementById("player");
const btnDownload = document.getElementById("btn-download");

let shownRecording = null;

function formatElapsed(seconds) {
  const m = Math.floor(seconds / 60).toString().padStart(2, "0");
  const s = Math.floor(seconds % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
}

function showMessage(text, isError) {
  messageEl.textContent = text;
  messageEl.className = isError ? "message error" : "message success";
}

async function refreshStatus() {
  const res = await fetch("/api/status");
  const data = await res.json();

  if (data.device_error) {
    statusEl.textContent = `Apparaatfout: ${data.device_error}`;
    btnRecord.disabled = true;
    btnStop.disabled = true;
    btnSend.disabled = true;
    playbackEl.hidden = true;
    return;
  }

  if (data.recording) {
    statusEl.textContent = "Bezig met opnemen...";
    timerEl.textContent = formatElapsed(data.elapsed);
    btnRecord.disabled = true;
    btnStop.disabled = false;
    btnSend.disabled = true;
    playbackEl.hidden = true;
    shownRecording = null;
  } else if (data.has_recording) {
    statusEl.textContent = `Opname klaar: ${data.last_recording}`;
    btnRecord.disabled = false;
    btnStop.disabled = true;
    btnSend.disabled = !data.backend_configured;
    if (!data.backend_configured) {
      showMessage("Backend-URL is niet ingesteld; versturen is uitgeschakeld.", true);
    }

    playbackEl.hidden = false;
    if (shownRecording !== data.last_recording) {
      shownRecording = data.last_recording;
      playerEl.src = `/api/recording/file?name=${encodeURIComponent(data.last_recording)}`;
      btnDownload.href = `/api/recording/file?download=1&name=${encodeURIComponent(data.last_recording)}`;
      btnDownload.download = data.last_recording;
    }
  } else {
    statusEl.textContent = "Klaar om op te nemen";
    timerEl.textContent = "00:00";
    btnRecord.disabled = false;
    btnStop.disabled = true;
    btnSend.disabled = true;
    playbackEl.hidden = true;
    shownRecording = null;
  }
}

async function post(url) {
  const res = await fetch(url, { method: "POST" });
  const data = await res.json();
  if (!data.ok) {
    showMessage(data.error || "Onbekende fout", true);
  }
  return data;
}

btnRecord.addEventListener("click", async () => {
  const data = await post("/api/record/start");
  if (data.ok) showMessage("Opname gestart", false);
  refreshStatus();
});

btnStop.addEventListener("click", async () => {
  const data = await post("/api/record/stop");
  if (data.ok) showMessage(`Opname gestopt (${data.duration}s)`, false);
  refreshStatus();
});

btnSend.addEventListener("click", async () => {
  showMessage("Bezig met versturen...", false);
  btnSend.disabled = true;
  const data = await post("/api/record/send");
  if (data.ok) showMessage("Opname verstuurd naar backend", false);
  refreshStatus();
});

setInterval(refreshStatus, 1000);
refreshStatus();
