import logging
import re
from typing import Any, List, Optional

from src.providers.base import ProductProvider, ProductData
from src.providers.ecommerce.amazon.openwebninja_client import OpenWebNinjaClient
from src.providers.ecommerce.amazon.models import (
    OpenWebNinjaSearchItem,
    OpenWebNinjaItemDetail,
)
from src.providers.ecommerce.amazon.exceptions import (
    AmazonInvalidResponseError,
    AmazonProviderError,
)

logger = logging.getLogger(__name__)


def parse_price(value: Any) -> Optional[float]:
    """Parse prices such as '₹1,999' or '1,999.50' into a float."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).replace(",", "")
    text = re.sub(r"[^0-9.]", "", text)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_availability(value: Any) -> bool:
    if value is None:
        return True
    text = str(value).strip().lower()
    if not text:
        return True
    if "out of stock" in text or "unavailable" in text or "currently unavailable" in text:
        return False
    return True


class OpenWebNinjaProvider(ProductProvider):
    """
    Amazon provider implementation using the OpenWeb Ninja Real-Time Amazon Data API.
    """

    def __init__(self):
        self.client = OpenWebNinjaClient()

    def _normalize_search_item(self, item: OpenWebNinjaSearchItem, platform: str) -> ProductData:
        try:
            return ProductData(
                source="openwebninja",
                platform=platform,
                source_product_id=item.asin,
                title=item.product_title,
                product_url=item.product_url,
                image_url=item.product_photo,
                category=item.category.name if item.category else None,
                current_price=parse_price(item.product_price) or 0.0,
                listed_price=parse_price(item.product_original_price),
                currency=item.currency or "INR",
                availability=parse_availability(item.product_availability),
            )
        except Exception as e:
            logger.error(f"Error normalizing OpenWeb Ninja search item {item.asin}: {str(e)}")
            raise AmazonInvalidResponseError(f"Search item normalization failed: {str(e)}")

    def _normalize_item_detail(self, item: OpenWebNinjaItemDetail, platform: str) -> ProductData:
        try:
            current_price = item.product_price_value
            if current_price is None:
                current_price = parse_price(item.product_price) or 0.0

            listed_price = item.product_original_price_value
            if listed_price is None:
                listed_price = parse_price(item.product_original_price)

            return ProductData(
                source="openwebninja",
                platform=platform,
                source_product_id=item.asin,
                title=item.product_title,
                category=item.category.name if item.category else None,
                description=item.product_description,
                product_url=item.product_url,
                image_url=item.product_photo,
                seller=item.seller or item.product_byline,
                current_price=float(current_price),
                listed_price=listed_price,
                currency=item.currency or "INR",
                availability=parse_availability(item.product_availability),
                model_number=item.model_number,
            )
        except Exception as e:
            logger.error(f"Error normalizing OpenWeb Ninja item detail {item.asin}: {str(e)}")
            raise AmazonInvalidResponseError(f"Item detail normalization failed: {str(e)}")

    async def search_products(self, query: str, platform: str) -> List[ProductData]:
        logger.info(f"Searching Amazon via OpenWeb Ninja for '{query}'")
        try:
            response = await self.client.search(query)
            products = []
            for item in response.data.products:
                try:
                    products.append(self._normalize_search_item(item, platform))
                except AmazonInvalidResponseError:
                    continue
            logger.info(f"OpenWeb Ninja returned {len(products)} Amazon products for '{query}'")
            return products
        except Exception as e:
            logger.error(f"OpenWeb Ninja search failed: {str(e)}")
            raise

    async def get_product(self, product_id: str, platform: str) -> Optional[ProductData]:
        logger.info(f"Fetching Amazon product {product_id} via OpenWeb Ninja")
        try:
            item = await self.client.get_item(product_id)
            return self._normalize_item_detail(item, platform)
        except AmazonProviderError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching Amazon product {product_id} via OpenWeb Ninja: {str(e)}")
            return None

    async def get_price(self, product_id: str, platform: str) -> Optional[float]:
        product = await self.get_product(product_id, platform)
        return product.current_price if product else None

    async def get_updates(self) -> List[ProductData]:
        return []
