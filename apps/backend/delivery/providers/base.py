from typing import Protocol, TypedDict


class CityData(TypedDict):
    ref: str
    name: str
    country: str  # ISO 3166-1 alpha-2, e.g. "UA", "PL"


class WarehouseData(TypedDict):
    ref: str
    name: str
    address: str
    postal_code: str


class DeliveryProviderClient(Protocol):
    """
    Interface every delivery provider client must implement.

    Only read access to the provider's city/warehouse directory is needed —
    this project doesn't create waybills through the API, the seller hands
    parcels to the courier directly. The synced data only powers the
    branch picker shown at checkout and the admin/order info.
    """

    def fetch_all_cities(self) -> list[CityData]:
        ...

    def fetch_warehouses(self, city_ref: str) -> list[WarehouseData]:
        ...
