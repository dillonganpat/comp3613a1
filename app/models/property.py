from typing import TYPE_CHECKING, Optional
from decimal import Decimal

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.user import User
    from app.models.review import Review


class PropertyBase(SQLModel):
    title: str = Field(index=True)
    location: str = Field(index=True)
    description: str
    image_url: Optional[str] = Field(default=None)
    price_per_night: Decimal = Field(default=Decimal("0.00"), max_digits=10, decimal_places=2, ge=0)
    bedrooms: int = Field(default=1, ge=1)
    bathrooms: int = Field(default=1, ge=1)
    available: bool = True
    owner_id: int = Field(foreign_key="user.id")


class Property(PropertyBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    owner: Optional["User"] = Relationship(back_populates="properties")
    bookings: list["Booking"] = Relationship(
        back_populates="property",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    reviews: list["Review"] = Relationship(
        back_populates="property",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
