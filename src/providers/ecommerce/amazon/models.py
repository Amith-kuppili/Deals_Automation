from pydantic import BaseModel, Field
from typing import List, Optional


class OpenWebNinjaCategory(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None


class OpenWebNinjaSearchItem(BaseModel):
    """One entry of `data.products[]` from GET /search."""

    asin: str
    product_title: str
    product_price: Optional[str] = None
    product_original_price: Optional[str] = None
    currency: Optional[str] = None
    product_url: str
    product_photo: Optional[str] = None
    product_availability: Optional[str] = None
    category: Optional[OpenWebNinjaCategory] = None


class OpenWebNinjaSearchData(BaseModel):
    total_products: int = 0
    products: List[OpenWebNinjaSearchItem] = Field(default_factory=list)


class OpenWebNinjaSearchResponse(BaseModel):
    status: str = "OK"
    data: OpenWebNinjaSearchData


class OpenWebNinjaItemDetail(BaseModel):
    """GET /product-details -> data."""

    asin: str
    product_title: str
    product_price: Optional[str] = None
    product_price_value: Optional[float] = None
    product_original_price: Optional[str] = None
    product_original_price_value: Optional[float] = None
    currency: Optional[str] = None
    product_url: str
    product_photo: Optional[str] = None
    product_availability: Optional[str] = None
    product_byline: Optional[str] = None
    product_description: Optional[str] = None
    category: Optional[OpenWebNinjaCategory] = None
    model_number: Optional[str] = None
    seller: Optional[str] = None
