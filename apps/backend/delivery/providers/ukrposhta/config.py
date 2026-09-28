from dataclasses import dataclass

from django.conf import settings


@dataclass(frozen=True)
class UkrposhtaConfig:
    bearer_token: str
    api_url: str


def get_ukrposhta_config() -> UkrposhtaConfig:
    return UkrposhtaConfig(
        bearer_token=settings.UKRPOSHTA_BEARER_TOKEN,
        api_url=settings.UKRPOSHTA_API_URL,
    )
