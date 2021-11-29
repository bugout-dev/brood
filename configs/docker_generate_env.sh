#!/usr/bin/env sh

# Prepare Brood API application for docker-compose use

set -e

SCRIPT_DIR="$(realpath $(dirname $0))"
DOCKER_BROOD_DB_URI="postgresql://postgres:postgres@db/brood_dev"
DOCKER_BROOD_ENV_FILE="docker.brood.env"
DOCKER_BROOD_ALEMBIC_FILE="alembic.brood.ini"

# Generate environment variables

cp "$SCRIPT_DIR/sample.env" "$SCRIPT_DIR/$DOCKER_BROOD_ENV_FILE"

# Clean file with variables from export prefix and quotation marks
sed --in-place 's|^export * ||' "$SCRIPT_DIR/$DOCKER_BROOD_ENV_FILE"
sed --in-place 's|"||g' "$SCRIPT_DIR/$DOCKER_BROOD_ENV_FILE"

sed -i "s|^BROOD_DB_URI=.*|BROOD_DB_URI=$DOCKER_BROOD_DB_URI|" "$SCRIPT_DIR/$DOCKER_BROOD_ENV_FILE"

# Generate alembic config

cp "$SCRIPT_DIR/alembic.sample.ini" "$SCRIPT_DIR/$DOCKER_BROOD_ALEMBIC_FILE"

sed -i "s|^sqlalchemy.url =.*|sqlalchemy.url = $DOCKER_BROOD_DB_URI|" "$SCRIPT_DIR/$DOCKER_BROOD_ALEMBIC_FILE"
