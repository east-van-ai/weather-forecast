#!/bin/bash
set -e

# env -i clears HOME, so look it up before building PATH.
HOME="$(cd ~ && pwd)"
export HOME
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
LOG_FILE="$LOG_DIR/hourly.log"

mkdir -p "$LOG_DIR"

cd "$SCRIPT_DIR"
. ./setup-env-vars.sh

{
  echo "=== Run started at $(date) ==="
  weather-forecast version
  weather-forecast run --commit
  echo "=== Run ended at $(date) ==="
} >> "$LOG_FILE" 2>&1
