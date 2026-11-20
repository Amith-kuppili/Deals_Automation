import logging
from typing import List, Optional
from src.providers.base import ProductProvider, ProductData
from src.providers.ecommerce.client import ECommerceClient
from src.providers.ecommerce.models import SearchResponse, ItemResponse
from src.providers.ecommerce.constants import SOURCE_NAME
from src.providers.ecommerce.exceptions import ECommerceInvalidResponseError

logger = logging.getLogger(__name__)

class ECommerceProvider(ProductProvider):
    """
    Generic E-Commerce Provider that abstracts QuickCommerce API.
    """
    def __init__(self):
        self.client = ECommerceClient()

    def _normalize_search_item(self, item, platform: str) -> ProductData:
        """
        Normalizes a basic search result into ProductData.
        """
        try:
            return ProductData(
                source=SOURCE_NAME,
                platform=platform,
                source_product_id=item.id,
                title=item.title,
                product_url=item.url,
                image_url=item.image,
                category=item.category,
                current_price=item.price,
                listed_price=item.mrp,
                availability=item.availability
            )
        except Exception as e:
            logger.error(f"Error normalizing search item {item.id}: {str(e)}")
            raise ECommerceInvalidResponseError(f"Search item normalization failed: {str(e)}")

    def _normalize_item_detail(self, item: ItemResponse, platform: str) -> ProductData:
        """
        Normalizes detailed item data into ProductData.
        """
        try:
            return ProductData(
                source=SOURCE_NAME,
                platform=platform,
                source_product_id=item.id,
                title=item.title,
                brand=item.brand,
                category=item.category,
                subcategory=item.subcategory,
                description=item.description,
                product_url=item.url,
                image_url=item.image,
                seller=item.seller,
                current_price=item.price,
                listed_price=item.mrp,
                availability=item.availability,
                sku=item.sku,
                model_number=item.model_number,
                gtin=item.gtin
            )
        except Exception as e:
            logger.error(f"Error normalizing item detail {item.id}: {str(e)}")
            raise ECommerceInvalidResponseError(f"Item detail normalization failed: {str(e)}")

    async def search_products(self, query: str, platform: str) -> List[ProductData]:
        logger.info(f"Searching for '{query}' on platform '{platform}'")
        response = await self.client.search(platform, query)
        
        products = []
        for item in response.items:
            try:
                products.append(self._normalize_search_item(item, platform))
            except ECommerceInvalidResponseError:
                continue
        
        return products

    async def get_product(self, product_id: str, platform: str) -> Optional[ProductData]:
        logger.info(f"Fetching details for product {product_id} on platform {platform}")
        try:
            item = await self.client.get_item(platform, product_id)
            return self._normalize_item_detail(item, platform)
        except Exception as e:
            logger.error(f"Failed to get product {product_id}: {str(e)}")
            return None

    async def get_price(self, product_id: str, platform: str) -> Optional[float]:
        product = await self.get_product(product_id, platform)
        return product.current_price if product else None

    async def get_updates(self) -> List[ProductData]:
        # QuickCommerce API might not have a generic delta feed in this version
        # Returning empty list as we rely on targeted search/item calls
        return []
