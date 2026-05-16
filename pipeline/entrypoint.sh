#!/bin/sh
set -e

cd /app

if [ "${FAERS_AUTO_SYNC:-True}" = "True" ] && [ -n "${FAERS_FROM:-}" ] && [ -n "${FAERS_TO:-}" ]; then
  echo "Running pipeline FAERS sync for range ${FAERS_FROM}..${FAERS_TO}"
  python download_faers_data.py "$FAERS_FROM" "$FAERS_TO" --force
else
  echo "Pipeline FAERS sync skipped (set FAERS_AUTO_SYNC=True and define FAERS_FROM/FAERS_TO to enable)"
fi

exec uvicorn main:app --host 0.0.0.0 --port 8000
