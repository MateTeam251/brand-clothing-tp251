from django.contrib import admin

from payments.models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "provider_order_reference",
        "currency",
        "amount",
        "provider",
        "status",
        "payment_url",
        "payment_data",
        "paid_at",
        "created_at",
    )

    list_filter = (
        "provider",
        "status",
        "created_at",
        "currency",
    )

    search_fields = (
        "provider_order_reference",
        "order__id",
        "order__email",
    )

    readonly_fields = (
        "order",
        "provider_order_reference",
        "currency",
        "amount",
        "provider",
        "payment_url",
        "payment_data",
        "paid_at",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Main Info",
            {
                "fields": (
                    "order",
                    "provider_order_reference",
                    "amount",
                    "currency",
                    "status",
                )
            }
        ),
        (
            "Details",
            {
                "fields": (
                    "provider",
                    "payment_url",
                    "payment_data",
                    "paid_at",
                )
            }
        ),
        (
            "System",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            }
        )
    )

    ordering = ("-created_at",)
