import requests

from delivery.providers.ukrposhta.config import get_ukrposhta_config


class UkrposhtaClient:
    """
    Wraps Ukrposhta's Address Classifier REST API.

    NOTE: Ukrposhta only hands out API access after a manual approval in
    their developer cabinet (https://dev.ukrposhta.ua), and the exact
    resource paths/params below are our best-effort read of that API shape —
    confirm them against the credentials/docs you get back before relying on
    this in production. The bearer token goes in the config, everything else
    (pagination, response field names) may need a small adjustment here.
    """

    PAGE_LIMIT = 100

    def __init__(self, config=None):
        self._config = config or get_ukrposhta_config()

    def _get(self, path: str, params: dict | None = None) -> list[dict]:
        response = requests.get(
            f"{self._config.api_url}/{path}",
            params=params or {},
            headers={"Authorization": f"Bearer {self._config.bearer_token}"},
            timeout=(5, 30),
        )
        response.raise_for_status()
        return response.json()

    def fetch_all_cities(self) -> list[dict]:
        cities = []
        page = 1

        while True:
            batch = self._get("city", {"page": page, "limit": self.PAGE_LIMIT})

            if not batch:
                break

            cities.extend(
                {
                    "ref": str(city["id"]),
                    "name": city["name"],
                    "country": "UA",
                }
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
            batch = self._get("postoffice", {"city_id": city_ref, "page": page, "limit": self.PAGE_LIMIT})

            if not batch:
                break

            warehouses.extend(
                {
                    "ref": str(office["id"]),
                    "name": office.get("name", ""),
                    "address": office.get("address", ""),
                    "postal_code": office.get("postcode", ""),
                }
                for office in batch
            )

            if len(batch) < self.PAGE_LIMIT:
                break

            page += 1

        return warehouses
