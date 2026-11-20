import logging
from src.providers.mock_provider import MockProvider
from src.redis.celery_app import celery_app

logger = logging.getLogger(__name__)

class MockCollector:
    def __init__(self):
        self.provider = MockProvider()

    async def collect(self):
        logger.info("Starting mock collection...")
        products = await self.provider.get_updates()
        
        for product in products:
            # Send to Celery for processing
            # We pass the dict representation of ProductData
            celery_app.send_task(
                "process_product_update", 
                args=[product.model_dump()]
            )
            logger.info(f"Queued product for processing: {product.source_product_id}")
        
        logger.info(f"Collected {len(products)} products.")
