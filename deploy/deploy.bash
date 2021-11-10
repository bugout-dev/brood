#!/usr/bin/env bash

# Deployment script - intended to run on Brood servers

# Main
APP_DIR="${APP_DIR:-/home/ubuntu/app}"
AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"
PYTHON_ENV_DIR="${PYTHON_ENV_DIR:-/home/ubuntu/server-env}"
PYTHON="${PYTHON_ENV_DIR}/bin/python"
PIP="${PYTHON_ENV_DIR}/bin/pip"
SCRIPT_DIR="$(realpath $(dirname $0))"
PARAMETERS_SCRIPT="${SCRIPT_DIR}/parameters.py"
SECRETS_DIR="${SECRETS_DIR:-/home/ubuntu/secrets}"
PARAMETERS_ENV_PATH="${SECRETS_DIR}/app.env"
AWS_SSM_PARAMETER_PATH="${AWS_SSM_PARAMETER_PATH:-/brood/prod}"
SERVICE_FILE="${SCRIPT_DIR}/brood.service"

# Logging
LOGGER_SCRIPT="${SCRIPT_DIR}/logger.py"
RSYSLOG_CONF_FILE="/etc/rsyslog.d/brood.conf"
RSYSLOG_CONF_PORT=21514
RSYSLOG_CONF_SERVICE="brood"

set -eu

echo
echo
echo "Updating pip and setuptools"
"${PIP}" install -U pip setuptools

echo
echo
echo "Updating Python dependencies"
"${PIP}" install -e "${APP_DIR}/"

echo
echo
echo "Retrieving deployment parameters"
mkdir -p "${SECRETS_DIR}"
AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION}" "${PYTHON}" "${PARAMETERS_SCRIPT}" "${AWS_SSM_PARAMETER_PATH}" -o "${PARAMETERS_ENV_PATH}"

echo
echo
if [ -d "$(dirname $RSYSLOG_CONF_FILE)" ]; then
  echo "Setup rsyslog client"
  AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION}" "${PYTHON}" "${LOGGER_SCRIPT}" -o "${RSYSLOG_CONF_FILE}" -p "${RSYSLOG_CONF_PORT}" -s "${RSYSLOG_CONF_SERVICE}"
  systemctl restart rsyslog.service
else
  echo "Skipping rsyslog client setup"
fi

echo
echo
echo "Updating Python dependencies"
$PIP install -r "${APP_DIR}/requirements.txt"

echo
echo
echo "Replacing existing Brood service definition with ${SERVICE_FILE}"
chmod 644 "${SERVICE_FILE}"
cp "${SERVICE_FILE}" /etc/systemd/system/brood.service
systemctl daemon-reload
systemctl restart brood.service
systemctl status brood.service
