#!/usr/bin/env sh

# Generate server initial setup

set -e

# Create free group subscription, to be able create new groups
python -m brood.cli plans create \
  --name "Free plan" \
  --description "free plan description" \
  --default_units 5 \
  --plan_type "seats" \
  --public True \
  --kv_key BUGOUT_GROUP_FREE_SUBSCRIPTION_PLAN
