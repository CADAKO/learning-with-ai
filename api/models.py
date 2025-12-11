# api/models.py
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class Product:
    name: str
    price: Decimal
    original_price: Decimal
    id: Optional[int] = None  # ID может быть None при создании
    is_active: bool = True



@dataclass
class Coupon:
    code: str
    discount_percent: float
