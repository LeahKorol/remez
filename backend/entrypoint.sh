#!/bin/sh
set -e

cd /app

python manage.py migrate --noinput

if [ "${FAERS_AUTO_SYNC:-True}" = "True" ] && [ -n "${FAERS_FROM:-}" ] && [ -n "${FAERS_TO:-}" ]; then
	echo "Running FAERS sync for range ${FAERS_FROM}..${FAERS_TO}"
	python manage.py download_faers_data "$FAERS_FROM" "$FAERS_TO" --force
	python manage.py load_faers_terms "$FAERS_FROM" "$FAERS_TO"
else
	echo "FAERS sync skipped (set FAERS_AUTO_SYNC=True and define FAERS_FROM/FAERS_TO to enable)"
fi

exec python manage.py runserver 0.0.0.0:8000
