#!/usr/bin/env bash
# check_env.sh — validate a .env file without booting the app.
# Usage: bash scripts/check_env.sh [path/to/.env]
set -euo pipefail

ENV_FILE="${1:-.env}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: $ENV_FILE not found. Copy .env.example to .env and fill in values." >&2
  exit 1
fi

# Source the env file safely
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

ERRORS=()

# Required keys — app will refuse to start without these
REQUIRED=(
  POSTGRES_PASSWORD
  CROSSREF_MAILTO
  SECRET_KEY
)

for key in "${REQUIRED[@]}"; do
  val="${!key:-}"
  if [[ -z "$val" ]]; then
    ERRORS+=("MISSING: $key is required")
  fi
done

# SECRET_KEY length check
if [[ -n "${SECRET_KEY:-}" && ${#SECRET_KEY} -lt 32 ]]; then
  ERRORS+=("INVALID: SECRET_KEY must be at least 32 characters (currently ${#SECRET_KEY})")
fi

# Type checks
if [[ -n "${MAX_DAILY_LLM_COST_USD:-}" ]]; then
  if ! [[ "$MAX_DAILY_LLM_COST_USD" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
    ERRORS+=("INVALID: MAX_DAILY_LLM_COST_USD must be a number, got '$MAX_DAILY_LLM_COST_USD'")
  fi
fi

if [[ -n "${POSTGRES_PORT:-}" ]]; then
  if ! [[ "$POSTGRES_PORT" =~ ^[0-9]+$ ]]; then
    ERRORS+=("INVALID: POSTGRES_PORT must be an integer, got '$POSTGRES_PORT'")
  fi
fi

if [[ ${#ERRORS[@]} -gt 0 ]]; then
  echo "Environment validation FAILED:" >&2
  for err in "${ERRORS[@]}"; do
    echo "  $err" >&2
  done
  exit 1
fi

echo "OK: $ENV_FILE passes all checks."
