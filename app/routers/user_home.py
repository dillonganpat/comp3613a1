from decimal import Decimal

from fastapi import Request
from fastapi.responses import HTMLResponse

from app.dependencies import SessionDep
from app.dependencies.auth import AuthDep
from app.repositories.booking import BookingRepository
from app.repositories.property import PropertyRepository
from app.services.booking_service import BookingService
from app.services.property_service import PropertyService
from . import router, templates


@router.get("/app", response_class=HTMLResponse)
async def user_home_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    location = request.query_params.get("location", "").strip()
    min_price = request.query_params.get("min_price", "")
    max_price = request.query_params.get("max_price", "")

    property_service = PropertyService(PropertyRepository(db))
    bookings_service = BookingService(BookingRepository(db))
    listings = property_service.list_properties(
        location=location or None,
        min_price=Decimal(min_price) if min_price else None,
        max_price=Decimal(max_price) if max_price else None,
    )
    my_bookings = bookings_service.list_my_bookings(user.id)

    return templates.TemplateResponse(
        request=request,
        name="app.html",
        context={
            "user": user,
            "listings": listings,
            "my_bookings": my_bookings,
            "location": location,
            "min_price": min_price,
            "max_price": max_price,
        },
    )