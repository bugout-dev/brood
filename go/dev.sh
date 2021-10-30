#!/usr/bin/env sh

# Expects access to Go environment
set -e

BROOD_LISTENING_HOST="${BROOD_LISTENING_HOST:-127.0.0.1}"
BROOD_LISTENING_PORT="${BROOD_LISTENING_PORT:-7484}"

go run . -host "${BROOD_LISTENING_HOST}" -port "${BROOD_LISTENING_PORT}"
