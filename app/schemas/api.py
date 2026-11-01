"""Request/response models for the JSON API (/api/...)."""
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import EmailStr, Field
from sqlmodel import SQLModel


class ApiSignup(SQLModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class MessageResponse(SQLModel):
    message: str


class TokenResponse(SQLModel):
    access_token: str
    token_type: str = "bearer"


class PropertyCreate(SQLModel):
    title: str = Field(min_length=1, max_length=200)
    location: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    image_url: Optional[str] = None
    price_per_night: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    bedrooms: int = Field(default=1, ge=1)
    bathrooms: int = Field(default=1, ge=1)


class PropertyResponse(SQLModel):
    id: int
    title: str
    location: str
    description: str
    image_url: Optional[str] = None
    price_per_night: Decimal
    bedrooms: int
    bathrooms: int
    available: bool
    owner_id: int


class BookingCreate(SQLModel):
    property_id: int
    check_in: date
    check_out: date


class BookingResponse(SQLModel):
    id: int
    property_id: int
    tenant_id: int
    check_in: date
    check_out: date
    status: str
    total_price: Decimal
