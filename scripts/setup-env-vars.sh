# shellcheck shell=bash
# Sourced by cron-job.sh, never run on its own.

export SF_USERNAME="my.username@example.com"
export SF_CLIENT_ID="ThisIsMyClientID222..."
export SF_AUDIENCE="https://login.salesforce.com"

# Assign first: if the key file is missing, set -e stops the job here.
SF_SERVER_KEY="$(cat "/path/to/server.key")"
export SF_SERVER_KEY
