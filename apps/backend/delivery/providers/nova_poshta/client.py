import logging
import time
from collections.abc import Iterator

import requests

from delivery.providers.base import WarehouseData
from delivery.providers.nova_poshta.config import get_nova_poshta_config

logger = logging.getLogger(__name__)


class NovaPoshtaClient:
    """
    Wraps Nova Poshta's public JSON API (https://developers.novaposhta.ua),
    a single endpoint called with {modelName, calledMethod, methodProperties}.

    This only covers the Ukrainian network reachable through
    AddressGeneral/getWarehouses. Nova Poshta's EU network ("Nova Poshta
    Global") is a separate product with its own credentials/API that isn't
    wired in here.
    """

    PAGE_LIMIT = 500
    # Retried: NP rate limiting, timeouts, connection errors and 5xx answers.
    # Waits double on every retry: 5, 10, 20, 40, 80 s (~2.5 min at most per page).
    # Other API errors (bad key, bad request) fail at once.
    MAX_RETRIES = 5
    BACKOFF_SECONDS = 5

    def __init__(self, config=None):
        self._config = config or get_nova_poshta_config()

    def _call(self, model_name: str, called_method: str, method_properties: dict | None = None) -> list[dict]:
        payload = {
            "apiKey": self._config.api_key,
            "modelName": model_name,
            "calledMethod": called_method,
            "methodProperties": method_properties or {},
        }

        for attempt in range(self.MAX_RETRIES + 1):
            last_attempt = attempt == self.MAX_RETRIES

            try:
                response = requests.post(self._config.api_url, json=payload, timeout=(5, 30))
                response.raise_for_status()
            except (requests.Timeout, requests.ConnectionError) as error:
                if last_attempt:
                    raise
                self._wait(attempt, f"network error ({type(error).__name__})")
                continue
            except requests.HTTPError:
                if response.status_code < 500 or last_attempt:
                    raise
                self._wait(attempt, f"HTTP {response.status_code}")
                continue

            data = response.json()

            if data.get("success"):
                return data.get("data", [])

            errors = data.get("errors") or []
            # NP reports rate limiting in the body with HTTP 200 (spelled "To many requests").
            rate_limited = any("many requests" in str(error).lower() for error in errors)
            if not rate_limited or last_attempt:
                raise ValueError(f"Nova Poshta API error: {errors}")

            self._wait(attempt, "rate limit")

    def _wait(self, attempt: int, reason: str) -> None:
        delay = self.BACKOFF_SECONDS * 2 ** attempt
        logger.warning("Nova Poshta %s, retrying in %ss", reason, delay)
        time.sleep(delay)

    def iter_all_warehouses(self) -> Iterator[list[WarehouseData]]:
        """
        Yields every selectable warehouse in the country, one API page at a time.

        Fetched for the whole country rather than per city: ~110 requests of 500
        instead of one request per city (~11k cities), and only one page is held
        in memory at a time. City data comes with each warehouse, so getCities
        is not needed.
        """
        page = 1

        while True:
            batch = self._call(
                "AddressGeneral", "getWarehouses",
                {"Page": str(page), "Limit": str(self.PAGE_LIMIT)},
            )
            time.sleep(1)

            if not batch:
                break

            yield [
                {
                    "ref": warehouse["Ref"],
                    "name": warehouse["Description"],
                    "address": warehouse.get("ShortAddress", ""),
                    # PostalCodeUA is the postal index ("09012"); WarehouseIndex is NP's
                    # internal branch number ("12157/1"), checked against a live response.
                    "postal_code": warehouse.get("PostalCodeUA", ""),
                    "city_ref": warehouse["CityRef"],
                    # Includes the region, e.g. "Миньківці (Київська обл.)"
                    "city_name": warehouse["CityDescription"],
                    "country": "UA",
                }
                for warehouse in batch
                if self._is_selectable(warehouse)
            ]

            if len(batch) < self.PAGE_LIMIT:
                break

            page += 1

    @staticmethod
    def _is_selectable(warehouse: dict) -> bool:
        # Closed/suspended branches and ones NP marks as not selectable can't receive parcels.
        return warehouse.get("WarehouseStatus") == "Working" and warehouse.get("DenyToSelect") != "1"
