#!/usr/bin/env bash

# Deployment script - intended to run on Brood API server

# Colors
C_RESET='\033[0m'
C_RED='\033[1;31m'
C_GREEN='\033[1;32m'
C_YELLOW='\033[1;33m'

# Logs
PREFIX_INFO="${C_GREEN}[INFO]${C_RESET} [$(date +%d-%m\ %T)]"
PREFIX_WARN="${C_YELLOW}[WARN]${C_RESET} [$(date +%d-%m\ %T)]"
PREFIX_CRIT="${C_RED}[CRIT]${C_RESET} [$(date +%d-%m\ %T)]"

# Main
AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"
APP_DIR="${APP_DIR:-/home/ubuntu/brood}"
PYTHON_ENV_DIR="${PYTHON_ENV_DIR:-/home/ubuntu/brood-env}"
PYTHON="${PYTHON_ENV_DIR}/bin/python"
PIP="${PYTHON_ENV_DIR}/bin/pip"
SCRIPT_DIR="$(realpath $(dirname $0))"
PARAMETERS_SCRIPT="${SCRIPT_DIR}/parameters.py"
SECRETS_DIR="${SECRETS_DIR:-/home/ubuntu/brood-secrets}"
PARAMETERS_ENV_PATH="${SECRETS_DIR}/app.env"
AWS_SSM_PARAMETER_PATH="${AWS_SSM_PARAMETER_PATH:-/brood/prod}"

# API server service file
BROOD_SOURCE_SERVICE_FILE="brood.monolith.service"
BROOD_SERVICE_FILE="brood.service"

set -eu

echo
echo
echo -e "${PREFIX_INFO} Upgrading Python pip and setuptools"
"${PIP}" install --upgrade pip setuptools

echo
echo
echo -e "${PREFIX_INFO} Installing Python dependencies"
"${PIP}" install -e "${APP_DIR}/"

echo
echo
echo -e "${PREFIX_INFO} Retrieving deployment parameters"
mkdir -p "${SECRETS_DIR}"
AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION}" "${PYTHON}" "${PARAMETERS_SCRIPT}" "${AWS_SSM_PARAMETER_PATH}" -o "${PARAMETERS_ENV_PATH}"

echo
echo
echo -e "${PREFIX_INFO} Set correct permissions for app.env"
chmod 600 "${PARAMETERS_ENV_PATH}"

echo
echo
echo -e "${PREFIX_INFO} Replacing existing Brood service definition with ${BROOD_SERVICE_FILE}"
chmod 644 "${SCRIPT_DIR}/${BROOD_SOURCE_SERVICE_FILE}"
cp "${SCRIPT_DIR}/${BROOD_SOURCE_SERVICE_FILE}" "/home/ubuntu/.config/systemd/user/${BROOD_SERVICE_FILE}"
XDG_RUNTIME_DIR="/run/user/1000" systemctl --user daemon-reload
XDG_RUNTIME_DIR="/run/user/1000" systemctl --user restart "${BROOD_SERVICE_FILE}"
