from core.enums import DeliveryProvider
from delivery.providers.base import DeliveryProviderClient
from delivery.providers.nova_poshta.client import NovaPoshtaClient
from delivery.providers.ukrposhta.client import UkrposhtaClient

_PROVIDERS: dict[str, type[DeliveryProviderClient]] = {
    DeliveryProvider.NOVA_POSHTA: NovaPoshtaClient,
    DeliveryProvider.UKRPOSHTA: UkrposhtaClient,
}

# Providers whose city/branch directory gets synced and cached locally.
#
# DHL is intentionally left out: its EU network is far too large to bulk-sync
# city by city like Nova Poshta/Ukrposhta. If/when DHL is added, it needs an
# on-demand, address-based lookup (e.g. DHL's Service Point Locator, queried
# per checkout) instead of this cached-directory approach.
SYNCED_PROVIDERS: list[str] = list(_PROVIDERS.keys())


def get_provider(provider_code: str) -> DeliveryProviderClient:
    try:
        provider_cls = _PROVIDERS[provider_code]
    except KeyError:
        raise ValueError(f"No delivery provider client registered for '{provider_code}'")

    return provider_cls()
