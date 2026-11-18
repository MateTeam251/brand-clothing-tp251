import logging
import time

import requests
from celery import shared_task
from django.db import transaction
from django.utils import timezone

from delivery.factory import SYNCED_PROVIDERS, get_provider
from delivery.models import DeliveryCity, DeliveryBranch

logger = logging.getLogger(__name__)

# Celery runs with --pool=solo, which can't enforce time_limit: the sync
# stops itself instead. A normal run is a few minutes.
MAX_SYNC_SECONDS = 30 * 60

# Provider unreachable even after the client's own retries: run the whole sync
# again later instead of waiting for tomorrow.
SYNC_RETRY_DELAY_SECONDS = 30 * 60
SYNC_MAX_RETRIES = 2


@shared_task(bind=True, max_retries=SYNC_MAX_RETRIES)
def sync_provider_branches(self, provider_code: str):
    """
    Refreshes the cached branch directory of one provider.

    Each API page is upserted in bulk (a few queries per page instead of two
    per row). Branches that were not in this run are closed or removed by the
    provider and get deleted, but only after the whole run succeeded.
    """
    provider = get_provider(provider_code)
    started_at = timezone.now()
    started = time.monotonic()

    try:
        synced = _sync_pages(provider, provider_code, started)
    except requests.RequestException as error:
        # Nothing was deleted (deletes only after a full run), so retrying is safe.
        if self.request.retries >= SYNC_MAX_RETRIES:
            raise
        logger.warning(
            "Provider '%s' sync failed (%s), retry %s/%s in %ss.",
            provider_code, type(error).__name__, self.request.retries + 1, SYNC_MAX_RETRIES,
            SYNC_RETRY_DELAY_SECONDS,
        )
        raise self.retry(exc=error, countdown=SYNC_RETRY_DELAY_SECONDS)

    if not synced:
        # An empty directory means the API misbehaved, not that every branch closed.
        raise RuntimeError(f"Provider '{provider_code}' returned no branches, keeping the existing ones.")

    removed, _ = DeliveryBranch.objects.filter(provider=provider_code, last_synced_at__lt=started_at).delete()
    empty_cities, _ = DeliveryCity.objects.filter(provider=provider_code, branches__isnull=True).delete()

    logger.info(
        "Synced %s branches for provider '%s' in %.0fs (removed %s branches, %s empty cities).",
        synced, provider_code, time.monotonic() - started, removed, empty_cities,
    )
    return synced


def _sync_pages(provider, provider_code, started):
    """Saves every page; returns how many branches were saved."""
    synced = 0
    for page in provider.iter_all_warehouses():
        # Checked between pages; nothing is deleted on a stopped run (deletes only after success).
        if time.monotonic() - started > MAX_SYNC_SECONDS:
            raise RuntimeError(
                f"Provider '{provider_code}' sync stopped after {MAX_SYNC_SECONDS}s ({synced} branches saved)."
            )
        if page:
            _save_page(provider_code, page)
            synced += len(page)
    return synced


@transaction.atomic
def _save_page(provider_code, page):
    cities = {
        warehouse["city_ref"]: DeliveryCity(
            provider=provider_code,
            external_ref=warehouse["city_ref"],
            name=warehouse["city_name"],
            country=warehouse["country"],
        )
        for warehouse in page
    }
    DeliveryCity.objects.bulk_create(
        cities.values(),
        update_conflicts=True,
        unique_fields=["provider", "external_ref"],
        update_fields=["name", "country"],
    )
    city_ids = dict(
        DeliveryCity.objects.filter(provider=provider_code, external_ref__in=cities)
        .values_list("external_ref", "id")
    )

    DeliveryBranch.objects.bulk_create(
        [
            DeliveryBranch(
                provider=provider_code,
                external_ref=warehouse["ref"],
                city_id=city_ids[warehouse["city_ref"]],
                name=warehouse["name"],
                address=warehouse["address"],
                postal_code=warehouse["postal_code"],
            )
            for warehouse in page
        ],
        update_conflicts=True,
        unique_fields=["provider", "external_ref"],
        update_fields=["city", "name", "address", "postal_code", "last_synced_at"],
    )


@shared_task
def sync_all_providers():
    for provider_code in SYNCED_PROVIDERS:
        sync_provider_branches.delay(provider_code)
