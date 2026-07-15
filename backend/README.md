# Backend

Dit werkgebied bevat de verwerking van opnames met Azure AI Foundry en de API voor resultaten.

## Verantwoordelijkheden

- opnames ontvangen en valideren;
- audiobestanden transcriberen en sprekers onderscheiden;
- samenvatting, afspraken en actiepunten genereren;
- status, resultaten en fouten beschikbaar maken.

## Verwachte koppeling

- **Input:** audiobestand en metadata volgens `shared/contracts/`.
- **Output:** transcriptsegmenten met sprekers, samenvatting, afspraken en actiepunten.
- **Configuratie:** Azure-endpoints, deploymentnamen en secrets via omgevingsvariabelen.

## Lokaal starten

De backend gebruikt FastAPI, een SQLite-database en een afzonderlijk workerproces. De
recordingrij is tevens het duurzame jobrecord; er is geen Redis- of RQ-afhankelijkheid.

Installeer de dependencies in de bestaande virtual environment:

```bash
../.venv/bin/python -m pip install -e '.[dev]'
```

Start de HTTP-API vanuit deze map:

```bash
../.venv/bin/python -m uvicorn app.main:app --reload --port 8080
```

Start daarnaast een worker in een tweede terminal:

```bash
../.venv/bin/python -m app.worker
```

De API-documentatie is beschikbaar op `http://localhost:8080/docs`. De gedeelde
HTTP-overeenkomst staat in `../shared/contracts/openapi.yaml`.

### API-voorbeelden

Start eerst de API en worker zoals hierboven. De volgende voorbeelden gebruiken de
toegestane multi-speakerfixture uit `samples/test-data/` en gaan ervan uit dat de
commando's vanuit `backend/` worden uitgevoerd.

```bash
export API_URL=http://localhost:8080
```

Upload een opname. De response bevat een `id`; bewaar deze als `RECORDING_ID` voor
de resultaatsendpoints.

```bash
curl --fail-with-body -X POST "$API_URL/recordings" \
  -F 'title=Multi-speaker testopname' \
  -F 'recordedAt=2026-07-13T09:30:00Z' \
  -F 'locale=en-US' \
  -F 'audio=@../samples/test-data/multi-speaker-sequence.flac;type=audio/flac'
```

Bijvoorbeeld, als de upload `{"id":"rec_...","status":"queued"}` retourneert:

```bash
export RECORDING_ID=rec_vul_hier_de_upload_id_in
```

Vraag de opnamelijst op:

```bash
curl --fail-with-body "$API_URL/recordings"
```

Controleer de verwerkingsstatus. Blijf pollen tot `status` `completed` of `failed`
is; transcript, analyse en samenvatting retourneren `409` zolang de verwerking nog
niet klaar is.

```bash
curl --fail-with-body "$API_URL/recordings/$RECORDING_ID/status"
```

Haal het volledige transcript met sprekers en tijden op:

```bash
curl --fail-with-body "$API_URL/recordings/$RECORDING_ID/transcript"
```

Haal de samenvatting, afspraken, actiepunten en open vragen op:

```bash
curl --fail-with-body "$API_URL/recordings/$RECORDING_ID/summary"
```

Haal sentiment en key phrases op:

```bash
curl --fail-with-body "$API_URL/recordings/$RECORDING_ID/analysis"
```

### Configuratie

De volgende waarden zijn nodig voor volledige verwerking. Configureer ze uitsluitend
in de lokale omgeving of een secret store, nooit in de repository.

| Variabele | Doel |
| --- | --- |
| `SPEECH_ENDPOINT`, `SPEECH_API_KEY` | Azure Speech Fast Transcription |
| `LANGUAGE_ENDPOINT`, `LANGUAGE_API_KEY` | Azure AI Language sentiment en key phrases |
| `LLM_ENDPOINT`, `LLM_API_KEY`, `LLM_MODEL` | Anthropic Messages-compatibele samenvatting |
| `DATABASE_URL` | SQLite URL, standaard `sqlite:///./data/ezelsoor.db` |
| `STORAGE_PATH` | Lokale audio-opslag, standaard `./data/uploads` |
| `UPLOAD_MAX_BYTES` | Maximale uploadomvang, standaard 100 MiB |
| `DEFAULT_LOCALE` | Transcriptietaal, standaard `nl-NL` |

De worker verwerkt `queued` recordings als `transcribing`, daarna `analyzing`, en
markeert ze als `completed` of `failed`. Een verlopen workerlease wordt bij de
volgende claim opnieuw als `queued` behandeld.

### Tests

```bash
../.venv/bin/python -m pytest
```

## Bekende beperkingen

- Alleen lokale bestand- en SQLite-opslag zijn geïmplementeerd. Azure Blob Storage is
  een volgende stap voor gedeelde of persistente deployments.
- Er is nog geen authenticatie, conform het gedeelde OpenAPI-contract.
