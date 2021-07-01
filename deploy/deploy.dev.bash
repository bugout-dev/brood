#!/usr/bin/env bash

# Deployment script - intended to run on Brood development servers

# Main
APP_DIR="${APP_DIR:-/home/ubuntu/brood}"
AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"
PYTHON_ENV_DIR="${PYTHON_ENV_DIR:-/home/ubuntu/brood-env}"
PYTHON="${PYTHON_ENV_DIR}/bin/python"
PIP="${PYTHON_ENV_DIR}/bin/pip"
SCRIPT_DIR="$(realpath $(dirname $0))"
PARAMETERS_SCRIPT="${SCRIPT_DIR}/parameters.py"
SECRETS_DIR="${SECRETS_DIR:-/home/ubuntu/brood-secrets}"
DEV_ENV_PATH="${SECRETS_DIR}/dev.env"
PARAMETERS_ENV_PATH="${SECRETS_DIR}/app.env"
AWS_SSM_PARAMETER_PATH="${AWS_SSM_PARAMETER_PATH:-/brood/prod}"
SERVICE_FILE="${SCRIPT_DIR}/brood.dev.service"

set -eu

echo
echo
read -p "Run migration? [y/n]: " migration_answer
case "$migration_answer" in
    [yY1] ) 
    echo Running migration
    source $DEV_ENV_PATH
    source $PYTHON_ENV_DIR/bin/activate
    $APP_DIR/alembic.sh -c $APP_DIR/alembic.dev.ini upgrade head
    ;;
    [nN0] ) echo "Passing migration";;
    * ) echo "Unexpected answer, passing migration"
esac


echo
echo
read -p "Update environment variables? [y/n]: " env_answer
case "$env_answer" in
    [yY1] )
    echo "Preparing service environment variables"
    cp $DEV_ENV_PATH $PARAMETERS_ENV_PATH
    sed -i 's/export //g' $PARAMETERS_ENV_PATH
    ;;
    [nN0] ) echo "Passing environment variables update";;
    * ) echo "Unexpected answer, passing environment variables update"
esac

echo
echo
echo "Replacing existing Brood service definition with ${SERVICE_FILE}"
chmod 644 "${SERVICE_FILE}"
cp "${SERVICE_FILE}" /etc/systemd/system/brood.service
systemctl daemon-reload
systemctl restart brood.service
systemctl status brood.service
