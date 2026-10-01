from datetime import date
from decimal import Decimal

from app.models.booking import BookingBase, Booking
from app.repositories.booking import BookingRepository


class BookingService:
    def __init__(self, booking_repo: BookingRepository):
        self.booking_repo = booking_repo

    def create_booking(self, property_id: int, tenant_id: int, check_in: date, check_out: date,
                       total_price: Decimal) -> Booking:
        if check_in < date.today():
            raise ValueError("Check-in date cannot be in the past.")
        if check_out <= check_in:
            raise ValueError("Check-out must be after check-in.")
        if self.booking_repo.has_overlap(property_id, check_in, check_out):
            raise ValueError("This property is already booked for part of that date range.")

        booking_data = BookingBase(
            property_id=property_id,
            tenant_id=tenant_id,
            check_in=check_in,
            check_out=check_out,
            status="pending",
            total_price=total_price,
        )
        return self.booking_repo.create(booking_data)

    def list_my_bookings(self, tenant_id: int) -> list[Booking]:
        return self.booking_repo.list_by_tenant(tenant_id)
