from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException
from sqlalchemy import select, text
import redis.asyncio as redis_async
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.session import get_db, AsyncSessionLocal
from src.database.models import PriceHistory, DealScore
from src.redis.celery_app import celery_app
from src.workers.tasks import test_pipeline_task
from src.collectors.mock_collector import MockCollector
from src.collectors.ecommerce_collector import ECommerceCollector
from src.config.settings import settings
import logging
import asyncio

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Extreme Deal Hunter API")


@app.get("/health")
async def health_check():
    checks = {"database": "unknown", "redis": "unknown"}

    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = "error"
        logger.error("Database health check failed: %s", exc)

    redis_client = redis_async.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        await redis_client.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = "error"
        logger.error("Redis health check failed: %s", exc)
    finally:
        await redis_client.aclose()

    status = "healthy" if all(value == "ok" for value in checks.values()) else "degraded"
    payload = {
        "status": status,
        "checks": checks,
        "version": "0.1.0",
        "providers": {
            "ecommerce": "ENABLED" if settings.ECOMMERCE_API_ENABLED else "DISABLED",
            "amazon": {
                "enabled": settings.AMAZON_ENABLED,
                "country": settings.AMAZON_COUNTRY,
                "primary": settings.AMAZON_PRIMARY_PROVIDER,
                "backup": settings.AMAZON_BACKUP_PROVIDER,
                "openwebninja": "ENABLED" if settings.OPENWEBNINJA_ENABLED else "DISABLED",
                "brightdata": "ENABLED" if settings.BRIGHTDATA_ENABLED else "DISABLED"
            }
        }
    }

    if status != "healthy":
        raise HTTPException(status_code=503, detail=payload)
    return payload


@app.post("/test-task")
async def trigger_test_task(data: dict):
    task = test_pipeline_task.delay(data)
    return {"task_id": task.id, "status": "queued"}


@app.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    res = celery_app.AsyncResult(task_id)
    return {"task_id": task_id, "status": res.status, "result": res.result}


@app.get("/products/{product_id}/history")
async def get_product_history(product_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(PriceHistory).where(PriceHistory.product_id == product_id).order_by(PriceHistory.recorded_at.desc())
        )
        history = result.scalars().all()
        if not history:
            raise HTTPException(status_code=404, detail="Product history not found")

        return [
            {
                "price": h.price,
                "listed_price": h.listed_price,
                "recorded_at": h.recorded_at,
                "source": h.source
            } for h in history
        ]


@app.get("/products/{product_id}/deal")
async def get_product_deal(product_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(DealScore).where(DealScore.product_id == product_id).order_by(DealScore.created_at.desc()).limit(1)
        )
        deal = result.scalar_one_or_none()
        if not deal:
            raise HTTPException(status_code=404, detail="Deal score not found for this product")

        return {
            "classification": deal.classification,
            "score": deal.confidence * 100, # Simplified score
            "effective_discount": deal.effective_discount,
            "historical_median": deal.historical_median,
            "reason": deal.reason,
            "confidence": deal.confidence
        }


@app.post("/collect/mock")
async def trigger_mock_collection():
    collector = MockCollector()
    await collector.collect()
    return {"status": "collection_started"}


@app.post("/collect/ecommerce")
async def trigger_ecommerce_collection(payload: dict, background_tasks: BackgroundTasks):
    """
    Trigger E-Commerce collection.
    Payload: {"platform": "flipkart", "query": "wireless earbuds"}
    """
    platform = payload.get("platform")
    query = payload.get("query")

    if not platform or not query:
        raise HTTPException(status_code=400, detail="Missing 'platform' or 'query' in request body")

    if platform == "amazon":
        amazon_available = (
            settings.AMAZON_ENABLED
            or settings.OPENWEBNINJA_ENABLED
            or settings.BRIGHTDATA_ENABLED
        )
        if not amazon_available:
            raise HTTPException(status_code=400, detail="Amazon providers are disabled in settings")
    elif not settings.ECOMMERCE_API_ENABLED:
        raise HTTPException(status_code=400, detail="E-Commerce provider is disabled in settings")

    async def run_collection():
        collector = ECommerceCollector()
        logger.info(f"Running collection for {platform}: {query}")
        result = await collector.collect(platform, query)
        logger.info(f"Collection finished for {platform}: {result}")

    background_tasks.add_task(run_collection)
    return {"status": "collection_started", "platform": platform, "query": query}


@app.get("/")
async def root():
    return {"message": "Welcome to Extreme Deal Hunter API"}
