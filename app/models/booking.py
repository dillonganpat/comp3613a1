from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.property import Property
    from app.models.user import User


class BookingBase(SQLModel):
    property_id: int = Field(foreign_key="property.id")
    tenant_id: int = Field(foreign_key="user.id")
    check_in: date
    check_out: date
    status: str = "pending"
    total_price: Decimal = Field(default=Decimal("0.00"), max_digits=10, decimal_places=2, ge=0)


class Booking(BookingBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    property: Optional["Property"] = Relationship(back_populates="bookings")
    tenant: Optional["User"] = Relationship(back_populates="bookings")
