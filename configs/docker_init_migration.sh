#!/usr/bin/env sh

set -e

# Running alembic migrations to head (using config file specified 
# by the ALEMBIC_CONFIG environment variable)
if [ -z "$ALEMBIC_CONFIG" ]
then
    echo "Please explicitly set the ALEMBIC_CONFIG environment variable to point to an alembic configuration file"
    exit 1
fi

ALEMBIC_CONFIG="$ALEMBIC_CONFIG" sh alembic.sh upgrade head
