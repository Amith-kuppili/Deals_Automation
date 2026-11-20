import asyncio
import time
from typing import List, Optional
from src.providers.base import ProductProvider, ProductData

class MockProvider(ProductProvider):
    def __init__(self):
        # Predefined mock data to simulate an API
        self.mock_products = {
            "mock_1": {
                "source": "mock",
                "source_product_id": "mock_1",
                "platform": "mock",
                "title": "High-End Gaming Laptop",
                "category": "Electronics",
                "product_url": "http://mock.com/p1",
                "image_url": "http://mock.com/i1.jpg",
                "current_price": 4999.0,
                "listed_price": 50000.0,
                "seller": "MockStore",
                "availability": True,
                "timestamp": time.time(),
            },
            "mock_2": {
                "source": "mock",
                "source_product_id": "mock_2",
                "platform": "mock",
                "title": "Basic Cotton T-Shirt",
                "category": "Clothing",
                "product_url": "http://mock.com/p2",
                "image_url": "http://mock.com/i2.jpg",
                "current_price": 399.0,
                "listed_price": 5000.0,
                "seller": "FashionMock",
                "availability": True,
                "timestamp": time.time(),
            },
            "mock_3": {
                "source": "mock",
                "source_product_id": "mock_3",
                "platform": "mock",
                "title": "Noise Cancelling Headphones",
                "category": "Electronics",
                "product_url": "http://mock.com/p3",
                "image_url": "http://mock.com/i3.jpg",
                "current_price": 15000.0,
                "listed_price": 25000.0,
                "seller": "TechMock",
                "availability": True,
                "timestamp": time.time(),
            },
        }

    async def search_products(self, query: str, platform: str = "mock") -> List[ProductData]:
        # Simulate network delay
        await asyncio.sleep(0.1)
        results = [
            ProductData(**{**p, "platform": platform})
            for p in self.mock_products.values()
            if query.lower() in p["title"].lower()
        ]
        return results

    async def get_product(self, product_id: str, platform: str = "mock") -> Optional[ProductData]:
        await asyncio.sleep(0.1)
        p = self.mock_products.get(product_id)
        return ProductData(**{**p, "platform": platform}) if p else None

    async def get_price(self, product_id: str, platform: str = "mock") -> Optional[float]:
        await asyncio.sleep(0.1)
        p = self.mock_products.get(product_id)
        return p["current_price"] if p else None

    async def get_updates(self) -> List[ProductData]:
        await asyncio.sleep(0.1)
        # In a real scenario, this would fetch changed items
        return [ProductData(**p) for p in self.mock_products.values()]
