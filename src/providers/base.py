from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field
import time

class ProductData(BaseModel):
    source: str
    source_product_id: str
    platform: str
    title: str
    brand: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    description: Optional[str] = None
    product_url: str
    image_url: Optional[str] = None
    seller: Optional[str] = None
    current_price: float
    listed_price: Optional[float] = None
    currency: str = "INR"
    availability: bool = True
    sku: Optional[str] = None
    model_number: Optional[str] = None
    gtin: Optional[str] = None
    timestamp: float = Field(default_factory=lambda: time.time())

    model_config = ConfigDict(populate_by_name=True)

class ProductProvider(ABC):
    @abstractmethod
    async def search_products(self, query: str, platform: str) -> List[ProductData]:
        pass

    @abstractmethod
    async def get_product(self, product_id: str, platform: str) -> Optional[ProductData]:
        pass

    @abstractmethod
    async def get_price(self, product_id: str, platform: str) -> Optional[float]:
        pass

    @abstractmethod
    async def get_updates(self) -> List[ProductData]:
        pass
