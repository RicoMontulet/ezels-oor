# EzelsOor local runners
#   just              — list recipes
#   just all          — API + worker + frontend + jabra
#   just backend      — API + worker
#   just frontend     — dashboard
#   just jabra        — pi-client / Jabra recorder

set dotenv-load := false
set shell := ["bash", "-euo", "pipefail", "-c"]

backend_port := env("BACKEND_PORT", "8082")
frontend_port := env("FRONTEND_PORT", "8080")
jabra_port := env("JABRA_PORT", "5001")

default:
    @just --list

# Copy missing .env files from examples (never overwrites)
env:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ ! -f .env ]]; then cp .env.example .env && echo "created .env"; fi
    if [[ ! -f frontend/.env ]]; then cp frontend/.env.example frontend/.env && echo "created frontend/.env"; fi
    if [[ ! -f pi-client/.env ]]; then cp pi-client/.env.example pi-client/.env && echo "created pi-client/.env"; fi

# Install Python deps for all services
sync: env
    cd backend && uv sync --extra dev
    cd frontend && uv sync
    cd pi-client && uv sync

# Backend HTTP API (uvicorn)
api: env
    cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port {{ backend_port }}

# Backend processing worker
worker: env
    cd backend && uv run python -m app.worker

# API + worker together
backend: env
    #!/usr/bin/env bash
    set -euo pipefail
    trap 'kill 0' EXIT INT TERM
    echo "backend API  → http://0.0.0.0:{{ backend_port }}/docs"
    echo "worker       → polling queue"
    (cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port {{ backend_port }}) &
    (cd backend && uv run python -m app.worker) &
    wait

# Frontend dashboard
frontend: env
    #!/usr/bin/env bash
    set -euo pipefail
    export BACKEND_API_URL="${BACKEND_API_URL:-http://localhost:{{ backend_port }}}"
    export RECORDING_APP_URL="${RECORDING_APP_URL:-http://localhost:{{ jabra_port }}}"
    export PORT="{{ frontend_port }}"
    export HOST="${HOST:-0.0.0.0}"
    echo "frontend     → http://0.0.0.0:{{ frontend_port }}"
    cd frontend && uv run python app.py

# Pi / Jabra recorder (pi-client)
jabra: env
    #!/usr/bin/env bash
    set -euo pipefail
    export BACKEND_URL="${BACKEND_URL:-http://localhost:{{ backend_port }}/recordings}"
    export PORT="{{ jabra_port }}"
    export HOST="${HOST:-0.0.0.0}"
    echo "jabra        → http://0.0.0.0:{{ jabra_port }}"
    cd pi-client && uv run app.py

alias pi := jabra

# Everything: backend (API+worker) + frontend + jabra
all: env
    #!/usr/bin/env bash
    set -euo pipefail
    trap 'kill 0' EXIT INT TERM
    export BACKEND_API_URL="${BACKEND_API_URL:-http://localhost:{{ backend_port }}}"
    export RECORDING_APP_URL="${RECORDING_APP_URL:-http://localhost:{{ jabra_port }}}"
    export BACKEND_URL="${BACKEND_URL:-http://localhost:{{ backend_port }}/recordings}"
    echo "backend API  → http://0.0.0.0:{{ backend_port }}/docs"
    echo "frontend     → http://0.0.0.0:{{ frontend_port }}"
    echo "jabra        → http://0.0.0.0:{{ jabra_port }}"
    echo "Ctrl-C stops all"
    (cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port {{ backend_port }}) &
    (cd backend && uv run python -m app.worker) &
    (cd frontend && HOST=0.0.0.0 PORT={{ frontend_port }} BACKEND_API_URL="$BACKEND_API_URL" RECORDING_APP_URL="$RECORDING_APP_URL" uv run python app.py) &
    (cd pi-client && HOST=0.0.0.0 PORT={{ jabra_port }} BACKEND_URL="$BACKEND_URL" uv run app.py) &
    wait

# Smoke: upload sample fixture to the running backend
smoke:
    #!/usr/bin/env bash
    set -euo pipefail
    curl -sf "http://127.0.0.1:{{ backend_port }}/health" >/dev/null
    curl -sf -X POST "http://127.0.0.1:{{ backend_port }}/recordings" \
      -F 'title=just-smoke' -F 'locale=en-US' \
      -F "audio=@samples/test-data/multi-speaker-sequence.flac;type=audio/flac"
    echo
