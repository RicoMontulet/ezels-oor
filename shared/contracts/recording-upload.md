# Opname-upload

Contract tussen `pi-client/` en `backend/` voor het versturen van een opname.
Dit is een startpunt vanuit `pi-client/`; pas aan in overleg met het
backend-team zodra hun endpoint vaststaat.

## Request

```
POST {BACKEND_URL}
Content-Type: multipart/form-data
```

| Veld              | Type            | Omschrijving                                    |
| ----------------- | --------------- | ------------------------------------------------ |
| `audio`           | bestand         | WAV, 16 kHz, mono, 16-bit PCM                    |
| `recorded_at`     | string          | ISO 8601-tijdstip waarop de opname is gestopt    |
| `duration_seconds`| string (float)  | Duur van de opname in seconden                   |

## Response (verwacht)

- `2xx`: opname geaccepteerd voor verwerking.
- `4xx`/`5xx`: fout; body mag een JSON-veld `error` bevatten zodat de
  device-UI dit rechtstreeks kan tonen.
