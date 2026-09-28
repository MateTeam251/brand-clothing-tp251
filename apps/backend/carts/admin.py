from django.contrib import admin
from django.db.models import Sum, F, DecimalField
from django.db.models.functions import Coalesce

from carts.models import AbandonedCartSnapshot, AbandonedCartSnapshotItem, Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ("product", "size", "quantity", "added_at")
    readonly_fields = ("added_at",)
    autocomplete_fields = ("product",)
    can_delete = True


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "owner_display",
        "status",
        "items_count",
        "created_at",
        "updated_at",
        "abandoned_at",
        "converted_at",
    )
    list_filter = ("status", "created_at", "abandoned_at", "converted_at")
    search_fields = (
        "user__email",
        "user__username",
        "session_key",
    )
    readonly_fields = (
        "created_at", "updated_at", "abandoned_at", "converted_at",
        "abandoned_value_uah", "abandoned_value_usd",
    )
    ordering = ("-updated_at",)
    inlines = [CartItemInline]
    list_select_related = ("user",)

    @admin.display(description="Owner")
    def owner_display(self, obj):
        if obj.user:
            return obj.user.email
        return f"Guest ({obj.session_key[:8]}…)" if obj.session_key else "Guest (no session)"

    @admin.display(description="Items")
    def items_count(self, obj):
        return obj.items.count()

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("items")


class AbandonedCartSnapshotItemInline(admin.TabularInline):
    model = AbandonedCartSnapshotItem
    extra = 0
    can_delete = False
    fields = ("product", "product_name", "size", "quantity", "price_uah", "price_usd", "discount_percent")
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(AbandonedCartSnapshot)
class AbandonedCartSnapshotAdmin(admin.ModelAdmin):
    """Read-only: snapshots are analytics history written by the Celery task."""
    list_display = ("id", "cart", "is_guest", "items_count", "value_uah", "abandoned_at", "recovered_at")
    list_filter = ("is_guest", "abandoned_at", "recovered_at")
    list_select_related = ("cart",)
    ordering = ("-abandoned_at",)
    inlines = [AbandonedCartSnapshotItemInline]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
