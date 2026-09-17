from django.contrib import admin

from payments.models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "currency",
        "amount",
        "provider",
        "status",
        "transaction_id",
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
        "transaction_id",
        "order__id",
        "order__email",
    )

    readonly_fields = (
        "order",
        "currency",
        "amount",
        "provider",
        "transaction_id",
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
                    "transaction_id",
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
