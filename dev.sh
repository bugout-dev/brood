#!/usr/bin/env sh

# Sets up Brood API server
# Expects access to Python environment with the requirements 
# for this project installed.
set -e

BROOD_HOST="${BROOD_HOST:-127.0.0.1}"
BROOD_PORT="${BROOD_PORT:-7474}"
BROOD_APP_DIR="${BROOD_APP_DIR:-$PWD}"
BROOD_ASGI_APP="${BROOD_ASGI_APP:-brood.api:app}"
BROOD_UVICORN_WORKERS="${BROOD_UVICORN_WORKERS:-2}"

uvicorn --reload \
  --port "$BROOD_PORT" \
  --host "$BROOD_HOST" \
  --app-dir "$BROOD_APP_DIR" \
  --workers "$BROOD_UVICORN_WORKERS" \
  "$BROOD_ASGI_APP"
