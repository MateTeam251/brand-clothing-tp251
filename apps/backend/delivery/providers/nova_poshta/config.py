from dataclasses import dataclass

from django.conf import settings


@dataclass(frozen=True)
class NovaPoshtaConfig:
    api_key: str
    api_url: str


def get_nova_poshta_config() -> NovaPoshtaConfig:
    return NovaPoshtaConfig(
        api_key=settings.NOVA_POSHTA_API_KEY,
        api_url=settings.NOVA_POSHTA_API_URL,
    )
