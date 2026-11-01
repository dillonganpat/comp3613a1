"""JSON REST API (prefix /api). Authenticate with POST /api/auth, then send
``Authorization: Bearer <access_token>`` on protected routes.

Status codes: 200/201/204 success, 400 bad input or bad credentials,
401 missing/invalid token, 403 wrong role or not the owner, 404 not found,
409 booking dates conflict, 422 schema validation error.
"""
from decimal import Decimal

from fastapi import HTTPException, Response, status
from sqlalchemy.exc import IntegrityError

from app.dependencies import SessionDep
from app.dependencies.auth import ApiAdminDep, AuthDep
from app.repositories.booking import BookingRepository
from app.repositories.property import PropertyRepository
from app.repositories.user import UserRepository
from app.schemas.api import (
    ApiSignup,
    BookingCreate,
    BookingResponse,
    MessageResponse,
    PropertyCreate,
    PropertyResponse,
    TokenResponse,
)
from app.schemas.auth import SigninRequest
from app.services.auth_service import AuthService
from app.services.booking_service import BookingConflictError, BookingService
from app.services.property_service import PropertyService
from . import api_router


# ----------------------------------------------------------------- auth
@api_router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=MessageResponse)
def api_signup(payload: ApiSignup, db: SessionDep):
    auth_service = AuthService(UserRepository(db))
    try:
        auth_service.register_user(payload.username, payload.email, payload.password)
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username or email already exists")
    return {"message": "account created"}


@api_router.post("/auth", response_model=TokenResponse)
def api_auth(payload: SigninRequest, db: SessionDep):
    token = AuthService(UserRepository(db)).authenticate_user(payload.username, payload.password)
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid credentials")
    return {"access_token": token, "token_type": "bearer"}


# ----------------------------------------------------------- properties
@api_router.get("/properties", response_model=list[PropertyResponse])
def api_list_properties(
    db: SessionDep,
    location: str | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
):
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(status_code=422, detail="min_price cannot exceed max_price")
    service = PropertyService(PropertyRepository(db))
    return service.list_properties(location=location, min_price=min_price, max_price=max_price)


@api_router.get("/properties/{property_id}", response_model=PropertyResponse)
def api_get_property(property_id: int, db: SessionDep):
    property_obj = PropertyService(PropertyRepository(db)).get_property(property_id)
    if property_obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    return property_obj


@api_router.post("/properties", status_code=status.HTTP_201_CREATED, response_model=PropertyResponse)
def api_create_property(payload: PropertyCreate, db: SessionDep, landlord: ApiAdminDep):
    service = PropertyService(PropertyRepository(db))
    return service.create_property(
        owner_id=landlord.id,
        title=payload.title,
        location=payload.location,
        description=payload.description,
        price_per_night=payload.price_per_night,
        bedrooms=payload.bedrooms,
        bathrooms=payload.bathrooms,
        image_url=payload.image_url,
    )


@api_router.delete("/properties/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
def api_delete_property(property_id: int, db: SessionDep, landlord: ApiAdminDep):
    service = PropertyService(PropertyRepository(db))
    property_obj = service.get_property(property_id)
    if property_obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    if property_obj.owner_id != landlord.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only delete your own properties")
    if BookingRepository(db).has_bookings(property_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot delete a property that has bookings")
    service.delete_property(property_id, landlord.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ------------------------------------------------------------- bookings
@api_router.post("/bookings", status_code=status.HTTP_201_CREATED, response_model=BookingResponse)
def api_create_booking(payload: BookingCreate, db: SessionDep, user: AuthDep):
    if user.role == "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Landlords are not permitted to book properties")
    property_obj = PropertyRepository(db).get_by_id(payload.property_id)
    if property_obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    nights = (payload.check_out - payload.check_in).days
    service = BookingService(BookingRepository(db))
    try:
        return service.create_booking(
            property_id=payload.property_id,
            tenant_id=user.id,
            check_in=payload.check_in,
            check_out=payload.check_out,
            total_price=property_obj.price_per_night * nights,
        )
    except BookingConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@api_router.get("/bookings/mine", response_model=list[BookingResponse])
def api_my_bookings(db: SessionDep, user: AuthDep):
    return BookingService(BookingRepository(db)).list_my_bookings(user.id)
