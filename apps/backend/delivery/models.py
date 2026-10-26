from django.db import models
from django_countries.fields import CountryField
from core.enums import DeliveryProvider


class DeliveryCity(models.Model):
    """
    Cached city/settlement list, synced periodically from each provider's
    API. Used for the city autocomplete step before picking a branch.
    """
    provider = models.CharField(max_length=30, choices=DeliveryProvider.choices)
    country = CountryField()
    external_ref = models.CharField(max_length=100)  # city_ref in delivery_data
    name = models.CharField(max_length=150, db_collation="uk-x-icu")           # city

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["provider", "external_ref"], name="unique_city_per_provider"),
        ]
        indexes = [models.Index(fields=["provider", "country", "name"])]


class DeliveryBranch(models.Model):
    """
    Cached branch/warehouse list, synced periodically. This is what the
    user picks when delivery_type=BRANCH — the "get a full list" step.
    """
    provider = models.CharField(max_length=30, choices=DeliveryProvider.choices)
    city = models.ForeignKey(DeliveryCity, on_delete=models.CASCADE, related_name="branches")
    external_ref = models.CharField(max_length=100)  # warehouse_ref
    name = models.CharField(max_length=255)            # warehouse
    address = models.CharField(max_length=255, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    last_synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["provider", "external_ref"], name="unique_branch_per_provider"),
        ]
        indexes = [models.Index(fields=["provider", "city"]), models.Index(fields=["postal_code"])]
