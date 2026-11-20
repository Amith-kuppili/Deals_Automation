from src.config.settings import Settings
from src.main import app
from src.redis.celery_app import celery_app


def test_railway_database_url_is_asyncpg_compatible():
    settings = Settings(
        _env_file=None,
        DATABASE_URL="postgresql://railway:secret@postgres:5432/deal_hunter",
    )

    assert settings.DATABASE_URL.startswith("postgresql+asyncpg://")


def test_railway_redis_url_is_used_by_celery():
    settings = Settings(
        _env_file=None,
        REDIS_URL="redis://default:secret@redis.railway.internal:6379/0",
    )

    assert settings.CELERY_BROKER_URL == settings.REDIS_URL
    assert settings.CELERY_RESULT_BACKEND == settings.REDIS_URL


def test_deployment_task_registration():
    assert "collect_flipkart_updates" in celery_app.tasks
    assert "process_product_update" in celery_app.tasks

    beat_task = celery_app.conf.beat_schedule[
        "collect-flipkart-category-feeds"
    ]["task"]
    assert beat_task in celery_app.tasks


def test_fastapi_app_can_be_imported():
    assert app.title == "Extreme Deal Hunter API"
