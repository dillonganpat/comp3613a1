from decimal import Decimal

from app.models.property import PropertyBase, Property
from app.repositories.property import PropertyRepository


class PropertyService:
    def __init__(self, property_repo: PropertyRepository):
        self.property_repo = property_repo

    def create_property(self, owner_id: int, title: str, location: str, description: str,
                        price_per_night: Decimal, bedrooms: int, bathrooms: int,
                        image_url: str | None = None) -> Property:
        property_data = PropertyBase(
            title=title,
            location=location,
            description=description,
            image_url=image_url or None,
            price_per_night=price_per_night,
            bedrooms=int(bedrooms),
            bathrooms=int(bathrooms),
            available=True,
            owner_id=owner_id,
        )
        return self.property_repo.create(property_data)

    def list_properties(self, location: str | None = None, min_price: Decimal | None = None, max_price: Decimal | None = None) -> list[Property]:
        return self.property_repo.list_all(location=location, min_price=min_price, max_price=max_price)

    def get_property(self, property_id: int) -> Property | None:
        return self.property_repo.get_by_id(property_id)

    def list_by_owner(self, owner_id: int) -> list[Property]:
        return self.property_repo.list_by_owner(owner_id)

    def delete_property(self, property_id: int, user_id: int) -> bool:
        property_obj = self.property_repo.get_by_id(property_id)
        if not property_obj or property_obj.owner_id != user_id:
            return False
        return self.property_repo.delete(property_id)
