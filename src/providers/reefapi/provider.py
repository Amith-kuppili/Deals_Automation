import logging
from typing import List
from src.providers.base import ProductData
from src.providers.reefapi.client import ReefAPIClient
from src.providers.reefapi.models import ReefAPIPriceObservation
from src.providers.reefapi.exceptions import ReefAPIError

logger = logging.getLogger(__name__)

class ReefAPIProvider:
    """
    Provider for ReefAPI historical data bootstrap.
    """
    def __init__(self):
        self.client = ReefAPIClient()

    async def get_historical_observations(self, product_id: str, platform: str) -> List[ProductData]:
        """
        Fetches historical observations from ReefAPI and normalizes them into ProductData.
        """
        try:
            response = await self.client.get_historical_data(product_id, platform)
            
            observations = []
            for obs in response.history:
                # We normalize historical observations into ProductData 
                # but they will be stored as PriceHistory entries.
                observations.append(ProductData(
                    source="reefapi",
                    platform=platform,
                    source_product_id=product_id,
                    title="Historical Observation", # Title is not needed for history
                    product_url="", # URL not needed for history
                    current_price=obs.price,
                    currency="INR",
                    availability=obs.availability,
                    seller=obs.seller
                ))
            
            return observations
        except ReefAPIError as e:
            logger.error(f"ReefAPI bootstrap failed for {product_id}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during ReefAPI bootstrap for {product_id}: {str(e)}")
            return []
