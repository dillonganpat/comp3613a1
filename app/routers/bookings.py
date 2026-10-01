from datetime import date

from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies import SessionDep
from app.dependencies.auth import AuthDep
from app.repositories.booking import BookingRepository
from app.repositories.property import PropertyRepository
from app.services.booking_service import BookingService
from app.utilities.flash import flash
from . import router


@router.post("/bookings/create", response_class=HTMLResponse)
async def booking_create_action(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    property_id: int = Form(),
    check_in: date = Form(),
    check_out: date = Form(),
):
    property_repo = PropertyRepository(db)
    property = property_repo.get_by_id(property_id)
    if property is None:
        raise status.HTTP_404_NOT_FOUND

    today = date.today()
    if check_in < today:
        flash(request, "Check-in date cannot be in the past.", "danger")
        return RedirectResponse(url=request.url_for("property_detail_view", property_id=property_id), status_code=status.HTTP_303_SEE_OTHER)
    if check_out <= check_in:
        flash(request, "Check-out must be after check-in.", "danger")
        return RedirectResponse(url=request.url_for("property_detail_view", property_id=property_id), status_code=status.HTTP_303_SEE_OTHER)

    total_price = property.price_per_night * (check_out - check_in).days
    service = BookingService(BookingRepository(db))
    try:
        service.create_booking(
            property_id=property_id,
            tenant_id=user.id,
            check_in=check_in,
            check_out=check_out,
            total_price=total_price,
        )
    except ValueError as exc:
        flash(request, str(exc), "danger")
        return RedirectResponse(url=request.url_for("property_detail_view", property_id=property_id), status_code=status.HTTP_303_SEE_OTHER)

    flash(request, "Booking request submitted successfully.", "success")
    return RedirectResponse(
        url=request.url_for("user_home_view"),
        status_code=status.HTTP_303_SEE_OTHER,
    )
