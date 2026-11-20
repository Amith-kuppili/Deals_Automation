web: sh -c 'alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}'
worker: celery -A src.redis.celery_app worker --loglevel=info --pool=solo
beat: celery -A src.redis.celery_app beat --loglevel=info --schedule=/tmp/celerybeat-schedule
