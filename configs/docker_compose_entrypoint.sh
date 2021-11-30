#!/usr/bin/env sh

# Sets up Brood server for docker compose

set -e

# Running alembic migrations to head (using config file specified 
# by the ALEMBIC_CONFIG environment variable)
if [ -z "$ALEMBIC_CONFIG" ]
then
    echo "Please explicitly set the ALEMBIC_CONFIG environment variable to point to an alembic configuration file"
    exit 1
fi

ALEMBIC_CONFIG="$ALEMBIC_CONFIG" sh alembic.sh upgrade head

# Preapre server to be full functional
sh ./configs/docker_initial_setup.sh

# Running dev.sh (from the directory from which this script was called)
sh dev.sh

