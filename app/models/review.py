from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.property import Property
    from app.models.user import User


class ReviewBase(SQLModel):
    property_id: int = Field(foreign_key="property.id")
    user_id: int = Field(foreign_key="user.id")
    author_name: str
    rating: int = Field(default=5, ge=1, le=5)
    comment: str


class Review(ReviewBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    property: Optional["Property"] = Relationship(back_populates="reviews")
    user: Optional["User"] = Relationship(back_populates="reviews")
