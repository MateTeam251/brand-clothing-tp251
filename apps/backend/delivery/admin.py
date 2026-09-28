from django.contrib import admin

from delivery.models import DeliveryCity, DeliveryBranch
from delivery.tasks import sync_provider_branches


@admin.register(DeliveryCity)
class DeliveryCityAdmin(admin.ModelAdmin):
    list_display = ("name", "provider", "country", "external_ref")
    list_filter = ("provider", "country")
    search_fields = ("name", "external_ref")
    ordering = ("provider", "country", "name")


@admin.register(DeliveryBranch)
class DeliveryBranchAdmin(admin.ModelAdmin):
    list_display = ("name", "provider", "city", "postal_code", "last_synced_at")
    list_filter = ("provider", "city__country")
    search_fields = ("name", "address", "postal_code", "external_ref", "city__name")
    autocomplete_fields = ("city",)
    ordering = ("provider", "city", "name")

    actions = ("resync_branches",)

    @admin.action(description="Re-sync branches now (for the providers among selected rows)")
    def resync_branches(self, request, queryset):
        provider_codes = set(queryset.values_list("provider", flat=True))

        for provider_code in provider_codes:
            sync_provider_branches.delay(provider_code)

        self.message_user(
            request,
            f"Queued a re-sync for: {', '.join(sorted(provider_codes))}. "
            f"This runs in the background, refresh in a bit.",
        )
