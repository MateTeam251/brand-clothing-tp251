from collections.abc import Iterator
from typing import Protocol, TypedDict


class WarehouseData(TypedDict):
    ref: str
    name: str
    address: str
    postal_code: str
    city_ref: str
    city_name: str
    country: str  # ISO 3166-1 alpha-2, e.g. "UA"


class DeliveryProviderClient(Protocol):
    """
    Interface every delivery provider client must implement.

    Only read access to the provider's warehouse directory is needed —
    this project doesn't create waybills through the API, the seller hands
    parcels to the courier directly. The synced data only powers the
    branch picker shown at checkout and the admin/order info.
    """

    def iter_all_warehouses(self) -> Iterator[list[WarehouseData]]:
        """All warehouses of the network, page by page, each with its city."""
        ...
