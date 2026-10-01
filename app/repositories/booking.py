from datetime import date
from typing import Optional

from sqlmodel import Session, select

from app.models.booking import Booking


class BookingRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, booking_data: Booking) -> Booking:
        booking_db = Booking.model_validate(booking_data)
        self.db.add(booking_db)
        self.db.commit()
        self.db.refresh(booking_db)
        return booking_db

    def get_by_id(self, booking_id: int) -> Optional[Booking]:
        return self.db.get(Booking, booking_id)

    def has_overlap(self, property_id: int, check_in: date, check_out: date) -> bool:
        statement = select(Booking).where(
            Booking.property_id == property_id,
            Booking.check_in < check_out,
            Booking.check_out > check_in,
        )
        return self.db.exec(statement).first() is not None

    def list_by_tenant(self, tenant_id: int) -> list[Booking]:
        statement = select(Booking).where(Booking.tenant_id == tenant_id).order_by(Booking.check_in.desc())
        return self.db.exec(statement).all()
