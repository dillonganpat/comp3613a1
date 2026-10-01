from fastapi import Request
from fastapi.responses import HTMLResponse

from app.dependencies import SessionDep
from app.dependencies.auth import AdminDep
from app.repositories.property import PropertyRepository
from app.services.property_service import PropertyService
from . import router, templates


@router.get("/admin", response_class=HTMLResponse)
async def admin_home_view(
    request: Request,
    user: AdminDep,
    db: SessionDep,
):
    property_service = PropertyService(PropertyRepository(db))
    my_properties = property_service.list_by_owner(user.id)

    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "user": user,
            "properties": my_properties,
        },
    )
