# pi-client

Flask-app die op de Raspberry Pi 5 draait: neemt een gesprek op via een
aangesloten Jabra PHS002W en verstuurt het opnamebestand naar de backend.

## Verantwoordelijkheden

- microfoon (Jabra PHS002W) automatisch herkennen via ALSA;
- opname starten/stoppen via een eenvoudige webinterface;
- opname als WAV lokaal bewaren in `recordings/` (genegeerd door Git);
- opname versturen naar `BACKEND_URL` zodra die is geconfigureerd;
- fouten (apparaat, opname, versturen) zichtbaar maken in de UI.

## Vereisten

- Raspberry Pi OS met `alsa-utils` (bevat `arecord`, standaard aanwezig);
- Python 3.11+;
- Jabra PHS002W aangesloten via USB.

Controleer dat de Pi het apparaat ziet:

```bash
arecord -l
```

Je zou een regel met `Jabra` moeten zien, bijvoorbeeld:

```
card 1: PHS002W [Jabra PHS002W], device 0: USB Audio [USB Audio]
```

## Lokaal starten

```bash
cd pi-client
cp .env.example .env
# vul BACKEND_URL in (bv. http://localhost:8082/recordings)
uv run app.py
```

Open de UI op `http://localhost:5001` (poort 5001 — macOS AirPlay bezet vaak 5000).

## Configuratie (`.env`)

| Variabele          | Verplicht | Omschrijving                                                        |
| ------------------- | --------- | -------------------------------------------------------------------- |
| `BACKEND_URL`       | nee       | Endpoint dat de opname ontvangt. Leeg = versturen staat uit in de UI. |
| `AUDIO_DEVICE_HINT` | nee       | Substring om het ALSA-apparaat te herkennen (standaard `Jabra`).      |
| `AUDIO_DEVICE`      | nee       | Forceer een ALSA-apparaat (bv. `plughw:1,0`) en sla autodetectie over.|
| `HOST` / `PORT`     | nee       | Waar Flask op luistert (standaard `0.0.0.0:5001`).                    |
| `MAX_RECORDINGS`    | nee       | Max lokale WAV-bestanden; oudere worden weggegooid (standaard `20`).  |
| `RECORDINGS_DIR`    | nee       | Map voor WAV-bestanden (standaard `pi-client/recordings/`).           |

## Input / output

- **Input:** knoppen "Opnemen", "Stop" en "Verstuur naar backend" in de browser.
- **Output:** WAV-bestand (16 kHz, mono, 16-bit PCM) via multipart POST naar
  `BACKEND_URL`, volgens [`shared/contracts/recording-upload.md`](../shared/contracts/recording-upload.md).

## API voor andere services

Opname starten/stoppen kan ook zonder de browser-UI, bijvoorbeeld door een
andere service op de Pi (fysieke knop, orchestrator, ...). Alle endpoints zijn
gewone JSON-POSTs zonder authenticatie of sessies:

| Endpoint                  | Methode | Omschrijving                                         |
| -------------------------- | ------- | ----------------------------------------------------- |
| `/api/record/start`        | POST    | Start een opname.                                     |
| `/api/record/stop`         | POST    | Stopt de opname; retourneert bestandsnaam en duur.     |
| `/api/record/send`         | POST    | Verstuurt de laatste opname naar `BACKEND_URL`.        |
| `/api/status`              | GET     | Huidige status: aan het opnemen, laatste opname, fouten.|
| `/api/recording/file`      | GET     | Laatste opname als audio (voor afspelen).              |
| `/api/recording/file?download=1` | GET | Laatste opname als download (`Content-Disposition: attachment`). |

```bash
curl -X POST http://<pi-ip>:5000/api/record/start
curl -X POST http://<pi-ip>:5000/api/record/stop
```

## Bekende beperkingen

- Eén opname tegelijk; na geslaagd versturen wordt het lokale WAV verwijderd.
  Oude lokale bestanden worden ook beperkt via `MAX_RECORDINGS`.
- Geen authenticatie op het versturen naar de backend; nog niet nodig voor de
  hackathondemo maar niet geschikt voor productie.
- Contract in `shared/contracts/recording-upload.md` is een voorstel vanuit dit
  onderdeel; nog niet afgestemd met het backend-team.
