from src.redis.celery_app import celery_app
from src.database.session import AsyncSessionLocal
from src.database.models import AlertHistory, Product, PriceHistory, DealScore
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import logging
import asyncio
from datetime import datetime, timezone

from src.data_engine.sufficiency import HistorySufficiencyEngine
from src.data_engine.bootstrap import ReefAPIBootstrapManager
from src.data_engine.deal.scorer import DealScorer
from src.notifications.telegram import TelegramNotifier
from src.config.settings import settings

logger = logging.getLogger(__name__)

@celery_app.task(name="test_pipeline_task")
def test_pipeline_task(data: dict):
    logger.info(f"Processing test task with data: {data}")
    return {"status": "success", "received_data": data}


@celery_app.task(name="collect_flipkart_updates")
def collect_flipkart_updates():
    """Collect scheduled Flipkart feed updates."""
    if not settings.FLIPKART_ENABLED:
        return {"status": "skipped", "reason": "flipkart_disabled"}
    return asyncio.run(_collect_flipkart_updates_async())


async def _collect_flipkart_updates_async():
    from src.collectors.ecommerce_collector import ECommerceCollector

    collector = ECommerceCollector()
    provider = await collector._get_provider("flipkart")
    products = await provider.get_updates()

    for product in products:
        process_product_update.delay(product.model_dump())

    return {"status": "queued", "products": len(products)}

@celery_app.task(name="process_product_update")
def process_product_update(product_data: dict):
    # Celery tasks are typically sync, so we use asyncio.run for async DB operations
    return asyncio.run(_process_product_update_async(product_data))

async def _process_product_update_async(product_data: dict):
    logger.info(f"Processing product update for {product_data['source_product_id']}")
    
    async with AsyncSessionLocal() as session:
        # 1. Upsert Product
        result = await session.execute(
            select(Product).where(
                Product.source == product_data['source'],
                Product.platform == product_data['platform'],
                Product.source_product_id == product_data['source_product_id']
            )
        )
        product = result.scalar_one_or_none()
        
        if not product:
            product = Product(
                source=product_data['source'],
                platform=product_data['platform'],
                source_product_id=product_data['source_product_id'],
                title=product_data['title'],
                category=product_data['category'],
                url=product_data['product_url'],
                image_url=product_data.get('image_url'),
                brand=product_data.get('brand', 'Unknown') 
            )
            session.add(product)
            await session.flush()
        else:
            product.title = product_data['title']
            product.category = product_data['category']
            product.url = product_data['product_url']
            product.image_url = product_data.get('image_url')

        # 2. Record Price History
        # Deduplication: Only store if price changed from last observation
        last_price_result = await session.execute(
            select(PriceHistory.price)
            .where(PriceHistory.product_id == product.id)
            .order_by(PriceHistory.recorded_at.desc())
            .limit(1)
        )
        last_price = last_price_result.scalar()

        if last_price is None or last_price != product_data['current_price']:
            price_entry = PriceHistory(
                product_id=product.id,
                price=product_data['current_price'],
                listed_price=product_data.get('listed_price'),
                seller=product_data.get('seller'),
                availability="available" if product_data.get('availability') else "unavailable",
                source=product_data['source']
            )
            session.add(price_entry)
            logger.info(f"Price changed for {product.source_product_id} to {product_data['current_price']}. Recording history.")
        else:
            logger.info(f"Price unchanged for {product.source_product_id} ({last_price}). Skipping history record.")
        
        await session.commit()
        logger.info(f"Saved product {product.source_product_id} and its price to DB.")

        # 3. Deal Scoring Pipeline
        try:
            # a. Check History Sufficiency
            # Count local observations
            hist_result = await session.execute(
                select(func.count(PriceHistory.id)).where(PriceHistory.product_id == product.id)
            )
            count = hist_result.scalar() or 0
            
            sufficiency_engine = HistorySufficiencyEngine()
            sufficiency = sufficiency_engine.evaluate(count)
            
            # b. Optional ReefAPI Bootstrap
            if not sufficiency.is_sufficient:
                bootstrap_manager = ReefAPIBootstrapManager()
                imported = await bootstrap_manager.bootstrap_product(product)
                if imported > 0:
                    logger.info(f"Bootstrapped {imported} observations from ReefAPI for product {product.id}")
                    # Update count after bootstrap
                    hist_result = await session.execute(
                        select(func.count(PriceHistory.id)).where(PriceHistory.product_id == product.id)
                    )
                    count = hist_result.scalar() or 0

            # c. Calculate and Save Deal Score
            scorer = DealScorer(session)
            deal_score = await scorer.score_product(product, product_data['current_price'])
            
            if deal_score:
                session.add(deal_score)
                await session.commit()
                logger.info(f"Calculated deal score for {product.source_product_id}: {deal_score.classification}")
                await _deliver_telegram_alert(session, product, deal_score)
            
        except Exception as e:
            logger.error(f"Deal scoring pipeline failed for {product.id}: {str(e)}")
            # We don't raise here to avoid failing the main product update
        
        return f"Product {product.source_product_id} processed and scored."


async def _deliver_telegram_alert(
    session,
    product: Product,
    deal_score: DealScore,
) -> None:
    """Send qualifying Telegram alerts once per deal score."""
    if deal_score.classification not in {"GOOD_DEAL", "EXTREME_DEAL"}:
        return

    notifier = TelegramNotifier()
    if not notifier.enabled:
        return

    existing = await session.execute(
        select(AlertHistory).where(
            AlertHistory.deal_score_id == deal_score.id,
            AlertHistory.channel == "telegram",
        )
    )
    alert = existing.scalar_one_or_none()
    if alert and alert.status == "sent":
        return

    if alert is None:
        alert = AlertHistory(
            product_id=product.id,
            deal_score_id=deal_score.id,
            channel="telegram",
            status="pending",
        )
        session.add(alert)
        await session.flush()

    message = (
        f"{deal_score.classification}: {product.title}\n"
        f"Current price: {deal_score.current_price:.2f}\n"
        f"Historical median: {deal_score.historical_median:.2f}\n"
        f"Discount: {deal_score.effective_discount:.1%}\n"
        f"{product.url}"
    )

    try:
        alert.message_id = await notifier.send_message(message)
        alert.status = "sent"
        alert.sent_at = datetime.now(timezone.utc)
        alert.error_message = None
    except Exception as exc:
        alert.status = "failed"
        alert.error_message = str(exc)
        logger.exception("Telegram alert failed for product %s", product.id)

    await session.commit()
