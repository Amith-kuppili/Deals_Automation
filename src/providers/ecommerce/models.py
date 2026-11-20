from pydantic import BaseModel, Field
from typing import List, Optional, Any

class SearchRequest(BaseModel):
    platform: str
    query: str
    page: Optional[int] = 1
    limit: Optional[int] = 20

class SearchItemResponse(BaseModel):
    id: str
    title: str
    price: float
    mrp: Optional[float] = None
    url: str
    image: Optional[str] = None
    category: Optional[str] = None
    availability: bool = True

class SearchResponse(BaseModel):
    total: int
    items: List[SearchItemResponse]
    page: int
    limit: int

class ItemRequest(BaseModel):
    platform: str
    item_id: str

class ItemResponse(BaseModel):
    id: str
    title: str
    brand: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    description: Optional[str] = None
    url: str
    image: Optional[str] = None
    price: float
    mrp: Optional[float] = None
    seller: Optional[str] = None
    availability: bool = True
    sku: Optional[str] = None
    model_number: Optional[str] = None
    gtin: Optional[str] = None

class CreditResponse(BaseModel):
    credits_remaining: int
    reset_date: Optional[str] = None
