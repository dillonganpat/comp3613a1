from decimal import Decimal
from typing import Optional

from sqlmodel import Session, func, select

from app.models.property import Property


class PropertyRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, property_data: Property) -> Property:
        property_db = Property.model_validate(property_data)
        self.db.add(property_db)
        self.db.commit()
        self.db.refresh(property_db)
        return property_db

    def get_by_id(self, property_id: int) -> Optional[Property]:
        return self.db.get(Property, property_id)

    def list_all(self, location: str | None = None, min_price: Decimal | None = None, max_price: Decimal | None = None) -> list[Property]:
        statement = select(Property).where(Property.available.is_(True))
        if location:
            statement = statement.where(Property.location.ilike(f"%{location}%"))
        if min_price is not None:
            statement = statement.where(Property.price_per_night >= min_price)
        if max_price is not None:
            statement = statement.where(Property.price_per_night <= max_price)
        statement = statement.order_by(Property.price_per_night.asc())
        return self.db.exec(statement).all()

    def list_by_owner(self, owner_id: int) -> list[Property]:
        statement = select(Property).where(Property.owner_id == owner_id).order_by(Property.id.desc())
        return self.db.exec(statement).all()

    def delete(self, property_id: int) -> bool:
        property_db = self.db.get(Property, property_id)
        if not property_db:
            return False
        self.db.delete(property_db)
        self.db.commit()
        return True
