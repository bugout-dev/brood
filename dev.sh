#!/usr/bin/env sh

# Expects access to Python environment with the requirements for this project installed.
set -e

BROOD_HOST="${BROOD_HOST:-0.0.0.0}"
BROOD_PORT="${BROOD_PORT:-7474}"

uvicorn --port "$BROOD_PORT" --host "$BROOD_HOST" brood.api:app --reload
