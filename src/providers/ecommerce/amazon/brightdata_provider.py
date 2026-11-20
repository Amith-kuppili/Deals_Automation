import logging
from typing import List, Optional, Any, Dict
from src.providers.base import ProductProvider, ProductData
from src.providers.ecommerce.amazon.brightdata_client import BrightDataClient
from src.providers.ecommerce.amazon.exceptions import (
    AmazonInvalidResponseError,
    AmazonProviderError,
)

logger = logging.getLogger(__name__)


class BrightDataProvider(ProductProvider):
    """
    Amazon provider implementation using Bright Data.
    """

    def __init__(self):
        self.client = BrightDataClient()

    def _normalize_search_item(self, item: Dict[str, Any], platform: str) -> ProductData:
        try:
            return ProductData(
                source="brightdata",
                platform=platform,
                source_product_id=item.get("asin"),
                title=item.get("title"),
                product_url=item.get("url"),
                image_url=item.get("image"),
                category=item.get("category"),
                current_price=float(item.get("price", 0)),
                listed_price=float(item.get("mrp", 0)) if item.get("mrp") else None,
                availability=item.get("availability", True)
            )
        except Exception as e:
            logger.error(f"Error normalizing Bright Data search item {item.get('asin')}: {str(e)}")
            raise AmazonInvalidResponseError(f"Search item normalization failed: {str(e)}")

    def _normalize_item_detail(self, item: Dict[str, Any], platform: str) -> ProductData:
        try:
            return ProductData(
                source="brightdata",
                platform=platform,
                source_product_id=item.get("asin"),
                title=item.get("title"),
                brand=item.get("brand"),
                category=item.get("category"),
                subcategory=item.get("subcategory"),
                description=item.get("description"),
                product_url=item.get("url"),
                image_url=item.get("image"),
                seller=item.get("seller"),
                current_price=float(item.get("price", 0)),
                listed_price=float(item.get("mrp", 0)) if item.get("mrp") else None,
                availability=item.get("availability", True),
                sku=item.get("sku"),
                gtin=item.get("gtin")
            )
        except Exception as e:
            logger.error(f"Error normalizing Bright Data item detail {item.get('asin')}: {str(e)}")
            raise AmazonInvalidResponseError(f"Item detail normalization failed: {str(e)}")

    async def search_products(self, query: str, platform: str) -> List[ProductData]:
        logger.info(f"Searching Amazon via Bright Data for '{query}'")
        try:
            response = await self.client.search(query)
            results = response.get("results", [])
            products = []
            for item in results:
                try:
                    products.append(self._normalize_search_item(item, platform))
                except AmazonInvalidResponseError:
                    continue
            return products
        except Exception as e:
            logger.error(f"Bright Data search failed: {str(e)}")
            raise

    async def get_product(self, product_id: str, platform: str) -> Optional[ProductData]:
        logger.info(f"Fetching Amazon product {product_id} via Bright Data")
        try:
            item = await self.client.get_item(product_id)
            return self._normalize_item_detail(item, platform)
        except AmazonProviderError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching Amazon product {product_id} via Bright Data: {str(e)}")
            return None

    async def get_price(self, product_id: str, platform: str) -> Optional[float]:
        product = await self.get_product(product_id, platform)
        return product.current_price if product else None

    async def get_updates(self) -> List[ProductData]:
        return []
