#!/bin/sh
set -e

log() {
	printf '%s [backend-entrypoint] %s\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" "$*"
}

run_step() {
	step_name="$1"
	shift
	log "START ${step_name}"
	if "$@"; then
		log "OK ${step_name}"
	else
		step_exit_code=$?
		log "FAIL ${step_name} (exit ${step_exit_code})"
		exit ${step_exit_code}
	fi
}

wait_for_server() {
	attempt=1
	max_attempts=30
	while [ "${attempt}" -le "${max_attempts}" ]; do
		if ! kill -0 "${server_pid}" 2>/dev/null; then
			return 1
		fi

		if python - <<'PY'
import socket

sock = socket.socket()
sock.settimeout(1)
try:
    sock.connect(("127.0.0.1", 8000))
except OSError:
    raise SystemExit(1)
finally:
    sock.close()
PY
		then
			return 0
		fi
		sleep 1
		attempt=$((attempt + 1))
	done

	return 1
}

start_server() {
	python manage.py runserver 0.0.0.0:8000 &
	server_pid=$!
	trap 'log "FAIL server received termination signal"; kill "${server_pid}" 2>/dev/null || true; wait "${server_pid}" 2>/dev/null || true; exit 143' INT TERM HUP

	if wait_for_server; then
		log "OK server listening on 0.0.0.0:8000"
	else
		log "FAIL server did not become ready on 0.0.0.0:8000"
		kill "${server_pid}" 2>/dev/null || true
		wait "${server_pid}" 2>/dev/null || true
		exit 1
	fi

	wait "${server_pid}"
	server_exit_code=$?
	if [ "${server_exit_code}" -ne 0 ]; then
		log "FAIL server exited unexpectedly (exit ${server_exit_code})"
		exit "${server_exit_code}"
	fi

	log "OK server exited cleanly"
}

log "START backend startup"
log "ENV DEBUG=${DEBUG:-unset} FAERS_AUTO_SYNC=${FAERS_AUTO_SYNC:-True} FAERS_FROM=${FAERS_FROM:-unset} FAERS_TO=${FAERS_TO:-unset}"
log "ENV DB_HOST=${DB_HOST:-unset} DB_PORT=${DB_PORT:-unset} PIPELINE_BASE_URL=${PIPELINE_BASE_URL:-unset} FRONTEND_URL=${FRONTEND_URL:-unset}"

cd /app

run_step "migrations" python manage.py migrate --noinput

if [ "${FAERS_AUTO_SYNC:-True}" = "True" ] && [ -n "${FAERS_FROM:-}" ] && [ -n "${FAERS_TO:-}" ]; then
	run_step "FAERS download ${FAERS_FROM}..${FAERS_TO}" python manage.py download_faers_data "$FAERS_FROM" "$FAERS_TO" --force
	run_step "FAERS load terms ${FAERS_FROM}..${FAERS_TO}" python manage.py load_faers_terms "$FAERS_FROM" "$FAERS_TO"
else
	log "SKIP FAERS sync (set FAERS_AUTO_SYNC=True and define FAERS_FROM/FAERS_TO to enable)"
fi

log "START server"
start_server
