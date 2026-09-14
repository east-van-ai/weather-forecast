#!/usr/bin/env bash

# Delete files according to the IDs in the file.

# Strict mode: exit on error, unset variable, or pipe failure.
set -euo pipefail

# --- Paths ---
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="$SCRIPT_DIR/data"

# --- Config (overridable via env) ---
TARGET_ORG="${TARGET_ORG:-my-weather-forecast-de-org}"

# --- Derived ---
DELETE_CANDIDATE_FILE="$DATA_DIR/old-files.csv"

# --hard-delete
# Deletes files permanently. Requires 'Bulk API Hard Delete' permission in your profile.
sf data delete bulk \
  --sobject ContentDocument \
  --target-org "$TARGET_ORG" \
  --file "$DELETE_CANDIDATE_FILE" \
  --hard-delete