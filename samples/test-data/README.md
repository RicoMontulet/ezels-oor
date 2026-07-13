# Audio-testdata

Deze map bevat drie korte clips uit de `test-clean`-split van LibriSpeech en één daarvan afgeleid multi-speakerbestand. De volledige set is kleiner dan 600 kB.

## Bestanden

- `1320-122617-0022.flac`: één spreker, 3,855 seconden.
- `260-123286-0000.flac`: één spreker, 7,040 seconden.
- `7729-102255-0039.flac`: één spreker, 6,815 seconden.
- `multi-speaker-sequence.flac`: bovenstaande clips achter elkaar, drie speakersegmenten, 17,710 seconden.
- `*.expected.json`: verwachte transcriptie, speakerlabels en tijden per gelijknamig audiobestand.

De drie teksten vormen samen geen natuurlijk gesprek. Het samengestelde bestand is alleen bedoeld als kleine technische test voor transcriptie en speaker diarization.

## Herkomst en licentie

De bronclips komen uit [LibriSpeech ASR corpus (OpenSLR SLR12)](https://www.openslr.org/12), via de [Hugging Face-datasetviewer](https://huggingface.co/datasets/openslr/librispeech_asr). LibriSpeech is samengesteld door Vassil Panayotov, Guoguo Chen, Daniel Povey en Sanjeev Khudanpur uit LibriVox-audioboeken.

LibriSpeech wordt verspreid onder de [Creative Commons Attribution 4.0 International-licentie](https://creativecommons.org/licenses/by/4.0/). Het samengestelde bestand is uitsluitend een concatenatie van de drie genoemde bronclips en valt onder dezelfde licentie.

## Verwachte uitvoer

Ieder `.expected.json`-bestand volgt het `TranscribeResult`-schema van de Azure Speech Fast Transcription API `2025-10-15`. De fixtures gebruiken de velden `durationMilliseconds`, `combinedPhrases` en `phrases`. Iedere phrase bevat `offsetMilliseconds`, `durationMilliseconds`, `text`, `locale` en een `speaker`-testlabel.

De speakerlabels zijn lokale verwachte labels. Azure kent speakergetallen per transcriptie zonder vaste volgorde toe; vergelijk diarization daarom op consistente sprekerwissels en niet op exacte nummers. `mai-transcribe-1` ondersteunt momenteel geen diarization en zal geen `speaker`-velden teruggeven. Gebruik een Azure Speech-model met diarization om alle fixturevelden te vergelijken.

De referentietranscripten komen uit LibriSpeech. Segmenttijden van het samengestelde bestand zijn gebaseerd op de grenzen tussen de bronclips; er zijn geen confidencewaarden of woordtimestamps toegevoegd.

## API-test voor deelnemers

Gebruik alleen eigen lokale `.env`; die is genegeerd door Git. Vul keys in vanuit `.env.example` en laad ze:

```bash
set -a
. ./.env
set +a
```

### 1. Speech Fast Transcription

Verstuur ieder `.flac`-bestand naar Azure Speech. Dit voorbeeld schrijft een response buiten repository; wijzig bestandsnaam per fixture.

```bash
curl --fail-with-body -X POST \
  "${SPEECH_ENDPOINT%s/}/speechtotext/transcriptions:transcribe?api-version=2025-10-15" \
  -H "Ocp-Apim-Subscription-Key: $SPEECH_API_KEY" \
  -F 'definition={"locales":["en-US"],"diarization":{"enabled":true,"maxSpeakers":3}};type=application/json' \
  -F 'audio=@samples/test-data/multi-speaker-sequence.flac;type=audio/flac' \
  -o /tmp/multi-speaker-response.json
```

Verwacht voor enkele clips één `speaker`-label. `multi-speaker-sequence.flac` geeft zes tekstphrases met drie labels: eerste bronclip speaker 1, middelste bronclip speaker 2, laatste bronclip speaker 3. Azure mag andere labelnummers gebruiken. Vergelijk tekst, tijdsgrenzen en wisselpatroon met `multi-speaker-sequence.expected.json`, niet op woordelijke interpunctie, exacte offsets, confidence of speakergetal.

### 2. Language-analyse

Neem `combinedPhrases[0].text` uit Speech-response als invoer. Azure AI Language analyseert tekst, geen audiobestanden. Voor sentiment is requestvorm:

```json
{
  "kind": "SentimentAnalysis",
  "analysisInput": {
    "documents": [{ "id": "clip", "language": "en", "text": "<Speech transcript>" }]
  },
  "parameters": { "opinionMining": true }
}
```

Post deze JSON naar `${LANGUAGE_ENDPOINT%s/}/language/:analyze-text?api-version=2024-11-01` met `Ocp-Apim-Subscription-Key` en `Content-Type: application/json`. Vervang `SentimentAnalysis` door `KeyPhraseExtraction` voor kernbegrippen. Verwacht respectievelijk document-/zinscores of `keyPhrases`; behandel zulke classificaties als modeloutput, niet als feiten.

### 3. Vertaling

Translator ontvangt eveneens Speech-tekst, bijvoorbeeld `[{"Text":"<Speech transcript>"}]`, en geen audio. Post dit naar `${TRANSLATOR_ENDPOINT%s/}/translate?api-version=3.0&from=en&to=nl` met headers `Ocp-Apim-Subscription-Key`, `Ocp-Apim-Subscription-Region: westeurope` en `Content-Type: application/json; charset=utf-8`. Verwacht een array met `translations[0].text`. Bewaar originele transcript, vertaling, tijden en sprekergegevens afzonderlijk.

### 4. LLM: samenvatten en vervolgvragen

`LLM_ENDPOINT`, `LLM_API_KEY`, `LLM_MODEL` en `LLM_MAX_TOKENS` configureren een Anthropic Messages-compatibel endpoint. Gebruik dit pas nadat Speech, Language en eventueel Translator de benodigde tekst hebben geleverd. Sonnet kan transcripties samenvatten, actiepunten en besluiten extraheren, vragen beantwoorden over een gesprek of gestructureerde JSON maken. Verstuur nooit secrets of niet-toegestane persoonsgegevens naar een model.

Voorbeeldrequest naar geconfigureerd Sonnet-model:

```bash
curl --fail-with-body -sS -X POST "$LLM_ENDPOINT" \
  -H "Content-Type: application/json" \
  -H "api-key: $LLM_API_KEY" \
  --data-binary @- <<JSON
{
  "model": "$LLM_MODEL",
  "system": "You are a helpful assistant.",
  "messages": [
    {
      "role": "user",
      "content": "Hello! How do I structure an API call?"
    }
  ],
  "temperature": 0.7,
  "max_tokens": ${LLM_MAX_TOKENS}
}
JSON
```

Vastgelegde voorbeeldresponse. `stop_reason: "max_tokens"` betekent dat antwoord door ingestelde limiet van 256 outputtokens is afgekapt; verhoog `LLM_MAX_TOKENS` wanneer volledig antwoord nodig is.

```json
{
  "id": "msg_011Ccz9QmZ9aJiBEAQBG7K2x",
  "container": null,
  "content": [
    {
      "citations": null,
      "text": "# Structuring an API Call\\n\\nHere's a general breakdown of the key components:\\n\\n## Basic Structure\\n\\n```\\n[METHOD] [Base URL]/[Endpoint]?[Query Parameters]\\nHeaders: [Key: Value]\\nBody: [Data]\\n```\\n\\n---\\n\\n## Key Components\\n\\n| Component | Description | Example |\\n|-----------|-------------|---------|\\n| **Method** | Type of request | `GET`, `POST`, `PUT`, `DELETE` |\\n| **Base URL** | Root address of the API | `https://api.example.com` |\\n| **Endpoint** | Specific resource path | `/users/123` |\\n| **Headers** | Metadata (auth, content type) | `Authorization: Bearer token` |\\n| **Query Params** | Filters added to URL | `?limit=10&page=2` |\\n| **Body** | Data sent with request | JSON payload |\\n\\n---\\n\\n## Common Examples\\n\\n**GET Request (fetch data)**\\n```http\\nGET https://api.example.com/users?limit=10\\nAuthorization: Bearer your_token\\n```\\n\\n**POST Request (send data)**\\n```http",
      "type": "text"
    }
  ],
  "model": "claude-sonnet-4-6",
  "role": "assistant",
  "stop_reason": "max_tokens",
  "stop_sequence": null,
  "type": "message",
  "usage": {
    "cache_creation": {
      "ephemeral_1h_input_tokens": 0,
      "ephemeral_5m_input_tokens": 0
    },
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 0,
    "inference_geo": "not_available",
    "input_tokens": 24,
    "output_tokens": 256,
    "server_tool_use": null,
    "service_tier": "standard"
  },
  "stop_details": null
}
```

## Vastgelegde testrun

[`api-responses.json`](api-responses.json) bevat volledige responses van 13 juli 2026 voor alle vier audiobestanden, plus sentiment-, key-phrase- en Engels-naar-Nederlands-requests op transcript van `multi-speaker-sequence.flac`. Publiceerde fixturedata is openbaar LibriSpeech; credentials zitten niet in bestand. Azure-modellen kunnen later andere tekst, timing, confidence, vertaling of analyse geven.
