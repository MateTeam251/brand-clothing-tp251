from django.contrib import admin

from orders.models import OrderItem, Order


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

    readonly_fields = (
        "product",
        "product_name",
        "size",
        "quantity",
        "fabric",
        "price_at_purchase",
        "discount_percent_at_purchase",
    )
    fields = readonly_fields

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user_name",
        "email",
        "status",
        "currency",
        "total_amount",
        "created_at",
    )

    list_filter = (
        "status",
        "currency",
        "created_at",
    )

    search_fields = (
        "id",
        "email",
        "user_name",
        "user_phone",
        "user__email",
    )

    readonly_fields = (
        "user",
        "user_name",
        "user_phone",
        "email",
        "delivery_address",
        "created_at",
        "currency",
        "subtotal",
        "discount_amount",
        "delivery_cost",
        "total_amount",
        "delivery_provider",
        "delivery_data",
        "updated_at",
    )

    fieldsets = (
        (
            "Customer Info",
            {
                "fields": (
                    "user",
                    "user_name",
                    "user_phone",
                    "email",
                    "delivery_address",
                )
            },
        ),
        (
            "Financial Details",
            {
                "fields": (
                    "currency",
                    "subtotal",
                    "discount_amount",
                    "delivery_cost",
                    "total_amount",
                )
            },
        ),
        (
            "Fulfillment & Delivery",
            {
                "fields": (
                    "status",
                    "delivery_provider",
                    "delivery_data",
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
            },
        ),
    )

    inlines = (OrderItemInline,)

    ordering = ("-created_at",)
