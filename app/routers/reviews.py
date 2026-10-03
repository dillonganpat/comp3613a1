from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies import SessionDep
from app.dependencies.auth import AuthDep
from app.models.review import Review
from app.utilities.flash import flash
from . import router


@router.post("/properties/{property_id}/reviews", response_class=HTMLResponse)
async def review_create_action(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    property_id: int,
    rating: int = Form(),
    comment: str = Form(),
):
    if user.role == "admin":
        flash(request, "Landlords cannot post reviews.", "danger")
        return RedirectResponse(
            url=request.url_for("property_detail_view", property_id=property_id),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    review = Review(
        property_id=property_id,
        user_id=user.id,
        author_name=user.username,
        rating=rating,
        comment=comment.strip(),
    )
    db.add(review)
    db.commit()

    flash(request, "Review posted successfully.", "success")
    return RedirectResponse(
        url=request.url_for("property_detail_view", property_id=property_id),
        status_code=status.HTTP_303_SEE_OTHER,
    )
