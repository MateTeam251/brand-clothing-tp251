import logging

from celery import shared_task

from delivery.factory import SYNCED_PROVIDERS, get_provider
from delivery.models import DeliveryCity, DeliveryBranch

logger = logging.getLogger(__name__)


@shared_task
def sync_provider_branches(provider_code: str):
    provider = get_provider(provider_code)

    for city_data in provider.fetch_all_cities():
        city, _ = DeliveryCity.objects.update_or_create(
            provider=provider_code,
            external_ref=city_data["ref"],
            defaults={
                "name": city_data["name"],
                "country": city_data["country"],
            },
        )
        for branch_data in provider.fetch_warehouses(city_data["ref"]):
            DeliveryBranch.objects.update_or_create(
                provider=provider_code,
                external_ref=branch_data["ref"],
                defaults={
                    "city": city,
                    "name": branch_data["name"],
                    "address": branch_data.get("address", ""),
                    "postal_code": branch_data.get("postal_code", ""),
                },
            )

    logger.info("Synced branches for provider '%s'.", provider_code)


@shared_task
def sync_all_providers():
    for provider_code in SYNCED_PROVIDERS:
        sync_provider_branches.delay(provider_code)
