import requests

from delivery.providers.nova_poshta.config import get_nova_poshta_config


class NovaPoshtaClient:
    """
    Wraps Nova Poshta's public JSON API (https://developers.novaposhta.ua),
    a single endpoint called with {modelName, calledMethod, methodProperties}.

    This only covers the Ukrainian network reachable through Address/getCities
    and AddressGeneral/getWarehouses. Nova Poshta's EU network ("Nova Poshta
    Global") is a separate product with its own credentials/API that isn't
    wired in here — plug it in as a second client once those docs are in hand.
    """

    PAGE_LIMIT = 500

    def __init__(self, config=None):
        self._config = config or get_nova_poshta_config()

    def _call(self, model_name: str, called_method: str, method_properties: dict | None = None) -> list[dict]:
        payload = {
            "apiKey": self._config.api_key,
            "modelName": model_name,
            "calledMethod": called_method,
            "methodProperties": method_properties or {},
        }

        response = requests.post(self._config.api_url, json=payload, timeout=(5, 30))
        response.raise_for_status()

        data = response.json()

        if not data.get("success"):
            raise ValueError(f"Nova Poshta API error: {data.get('errors')}")

        return data.get("data", [])

    def fetch_all_cities(self) -> list[dict]:
        cities = []
        page = 1

        while True:
            batch = self._call(
                "Address", "getCities",
                {"Page": str(page), "Limit": str(self.PAGE_LIMIT)},
            )

            if not batch:
                break

            cities.extend(
                {"ref": city["Ref"], "name": city["Description"], "country": "UA"}
                for city in batch
            )

            if len(batch) < self.PAGE_LIMIT:
                break

            page += 1

        return cities

    def fetch_warehouses(self, city_ref: str) -> list[dict]:
        warehouses = []
        page = 1

        while True:
            batch = self._call(
                "AddressGeneral", "getWarehouses",
                {"CityRef": city_ref, "Page": str(page), "Limit": str(self.PAGE_LIMIT)},
            )

            if not batch:
                break

            warehouses.extend(
                {
                    "ref": warehouse["Ref"],
                    "name": warehouse["Description"],
                    "address": warehouse.get("ShortAddress", ""),
                    # NB: field name for the postal index has moved around between
                    # Nova Poshta API versions — verify against a live response.
                    "postal_code": warehouse.get("WarehouseIndex", ""),
                }
                for warehouse in batch
            )

            if len(batch) < self.PAGE_LIMIT:
                break

            page += 1

        return warehouses
