#!/bin/sh
set -eu

ROLE="${SERVICE_ROLE:-api}"

case "$ROLE" in
  api)
    alembic upgrade head
    exec uvicorn src.main:app --host 0.0.0.0 --port "${PORT:-8000}"
    ;;
  worker)
    exec celery -A src.redis.celery_app worker --loglevel=info --pool=solo
    ;;
  beat)
    exec celery -A src.redis.celery_app beat --loglevel=info --schedule=/tmp/celerybeat-schedule
    ;;
  *)
    echo "Unknown SERVICE_ROLE='$ROLE'. Use api, worker, or beat." >&2
    exit 1
    ;;
esac
