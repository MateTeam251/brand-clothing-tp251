from core.enums import DeliveryProvider
from delivery.providers.base import DeliveryProviderClient
from delivery.providers.nova_poshta.client import NovaPoshtaClient

_PROVIDERS: dict[str, type[DeliveryProviderClient]] = {
    DeliveryProvider.NOVA_POSHTA: NovaPoshtaClient,
}

# Providers whose city/branch directory gets synced and cached locally.
SYNCED_PROVIDERS: list[str] = list(_PROVIDERS.keys())


def get_provider(provider_code: str) -> DeliveryProviderClient:
    try:
        provider_cls = _PROVIDERS[provider_code]
    except KeyError:
        raise ValueError(f"No delivery provider client registered for '{provider_code}'")

    return provider_cls()
