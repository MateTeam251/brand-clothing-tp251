from django.contrib import admin

from orders.email_services import send_order_status_changed_email
from orders.models import OrderItem, Order


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

    readonly_fields = (
        "product",
        "product_name",
        "size",
        "quantity",
        "fabric_composition_ua",
        "fabric_composition_eng",
        "price_at_purchase",
        "discount_percent_at_purchase",
        "unit_price_after_discount",
        "line_subtotal",
        "line_total",
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

    def save_model(self, request, obj: Order, form, change):
        old_status = None
        if change and "status" in form.changed_data:
            old_status = Order.objects.only("status").get(pk=obj.pk).status

        super().save_model(request, obj, form, change)

        if old_status is not None and old_status != obj.status:
            send_order_status_changed_email(obj)
