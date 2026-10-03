from datetime import date
from decimal import Decimal

from fastapi import Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies import SessionDep
from app.dependencies.auth import AdminDep, AuthDep
from app.repositories.property import PropertyRepository
from app.services.property_service import PropertyService
from app.utilities.flash import flash
from . import router, templates


@router.get("/properties/new", response_class=HTMLResponse)
async def property_new_view(
    request: Request,
    user: AdminDep,
    db: SessionDep,
):
    return templates.TemplateResponse(
        request=request,
        name="property_form.html",
        context={"user": user},
    )


@router.post("/properties/new", response_class=HTMLResponse)
async def property_create_action(
    request: Request,
    user: AdminDep,
    db: SessionDep,
    title: str = Form(),
    location: str = Form(),
    description: str = Form(),
    image_url: str | None = Form(default=None),
    price_per_night: Decimal = Form(),
    bedrooms: int = Form(),
    bathrooms: int = Form(),
):
    property_service = PropertyService(PropertyRepository(db))
    property_service.create_property(
        owner_id=user.id,
        title=title,
        location=location,
        description=description,
        price_per_night=price_per_night,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        image_url=image_url or None,
    )
    flash(request, f"Success! Your property '{title}' has been successfully posted.", "success")
    return RedirectResponse(
        url=request.url_for("admin_home_view"),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/properties/{property_id}/delete", response_class=HTMLResponse)
async def property_delete_action(
    request: Request,
    user: AdminDep,
    db: SessionDep,
    property_id: int,
):
    property_service = PropertyService(PropertyRepository(db))
    success = property_service.delete_property(property_id, user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete property")
    flash(request, "Property successfully deleted.", "success")
    return RedirectResponse(
        url=request.url_for("admin_home_view"),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/properties/{property_id}", response_class=HTMLResponse)
async def property_detail_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    property_id: int,
):
    property_service = PropertyService(PropertyRepository(db))
    property = property_service.get_property(property_id)
    if property is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    return templates.TemplateResponse(
        request=request,
        name="property_detail.html",
        context={
            "user": user,
            "property": property,
        },
    )
