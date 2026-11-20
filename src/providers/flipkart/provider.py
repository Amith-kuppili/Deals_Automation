import logging
import time
from typing import List, Optional, Dict, Any
from src.providers.base import ProductProvider, ProductData
from src.providers.flipkart.client import FlipkartClient
from src.config.settings import settings
from src.providers.flipkart.exceptions import FlipkartError, FlipkartNormalizationError

logger = logging.getLogger(__name__)

class FlipkartProvider(ProductProvider):
    """
    Implementation of the ProductProvider for Flipkart.
    Maps Flipkart API responses to the internal ProductData model.
    """
    def __init__(self):
        self.client = FlipkartClient()

    def _normalize_product(self, item: Dict[str, Any], platform: str = "flipkart") -> ProductData:
        """
        Maps a raw Flipkart product item to ProductData.
        """
        try:
            required_fields = ("productId", "title", "url", "price", "mrp")
            missing_fields = [field for field in required_fields if item.get(field) is None]
            if missing_fields:
                raise FlipkartNormalizationError(
                    f"Missing required fields: {', '.join(missing_fields)}"
                )

            # Note: Field names here are based on standard Affiliate API response schemas
            # If the API returns different field names, these should be adjusted.
            return ProductData(
                source="flipkart",
                source_product_id=str(item.get("productId", "")),
                platform=platform,
                title=item.get("title", "Unknown Product"),
                category=item.get("category", "General"),
                product_url=item.get("url", ""),
                image_url=item.get("image", ""),
                current_price=float(item.get("price", 0)),
                listed_price=float(item.get("mrp", 0)),
                seller=item.get("seller", None),
                availability=item.get("availability", True),
                timestamp=time.time()
            )
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Normalization error for product {item.get('productId')}: {str(e)}")
            raise FlipkartNormalizationError(f"Failed to normalize product: {str(e)}")

    async def search_products(self, query: str, platform: str = "flipkart") -> List[ProductData]:
        """
        Search for products on Flipkart and return normalized data.
        """
        response = await self.client.search_products(query)
        products = response.get("products", [])
        
        normalized = []
        for p in products:
            try:
                normalized.append(self._normalize_product(p, platform))
            except FlipkartNormalizationError:
                continue
        
        return normalized

    async def get_product(self, product_id: str, platform: str = "flipkart") -> Optional[ProductData]:
        """
        Fetch a single product by its ID.
        """
        try:
            item = await self.client.get_product_details(product_id)
            # The API might return a list or a single object
            product_raw = item if isinstance(item, dict) else (item[0] if item else None)
            
            if not product_raw:
                return None
                
            return self._normalize_product(product_raw, platform)
        except Exception as e:
            logger.error(f"Error fetching product {product_id}: {str(e)}")
            return None

    async def get_price(self, product_id: str, platform: str = "flipkart") -> Optional[float]:
        """
        Fetch only the current price for a product.
        """
        product = await self.get_product(product_id, platform)
        return product.current_price if product else None

    async def get_updates(self) -> List[ProductData]:
        """
        Fetch products from the configured Flipkart category feeds.

        The method is intentionally safe when Flipkart is disabled: Celery Beat
        can remain running without making an unauthenticated network request.
        """
        if not settings.FLIPKART_ENABLED:
            return []

        # This method is now handled by the Celery task directly to support 
        # delta feeds and ProviderSyncState.
        return []
