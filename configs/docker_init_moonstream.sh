#!/usr/bin/env sh

set -e

# Create user for Moonstream application
MOONSTREAM_USER="$(brood users create \
  --username moonstream \
  --email moonstream@example.com \
  --password moonstream --verified | jq -r .id)"

# Create token for Moonstream user
MOONSTREAM_TOKEN_ID="$(brood tokens create \
  --username moonstream | jq -r .id)"

# Create group for Moonstream application
MOONSTREAM_GROUP_ID="$(brood groups create \
  --name moonstream \
  --username moonstream | jq -r .id)"

# Create Moonstream application itself
MOONSTREAM_APPLICATION_ID="$(brood applications create \
  --group $MOONSTREAM_GROUP_ID \
  --name moonstream \
  --description moonstream | jq -r .id)"

VAR="$(cat <<EOF
export MOONSTREAM_ADMIN_ACCESS_TOKEN=$MOONSTREAM_TOKEN_ID
export MOONSTREAM_APPLICATION_ID=$MOONSTREAM_APPLICATION_ID
EOF
)"

echo "$VAR"
