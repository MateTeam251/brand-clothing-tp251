from django.contrib import admin
from django.utils.html import format_html

from products.models import (ProductType,
                             Product,
                             ProductImage,
                             SizeGuide,
                             Collection)


admin.site.register(ProductType)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image", "image_preview", "order")
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 80px;" />', obj.image.url)
        return "—"
    image_preview.short_description = "Preview"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name", "type", "collection", "price_uah", "discount_percent",
        "is_available", "is_bestseller", "is_new_collection",
    )
    list_editable = ("is_available", "is_bestseller", "is_new_collection")
    list_filter = ("is_available", "is_bestseller", "is_new_collection", "type", "collection")
    inlines = [ProductImageInline]
    search_fields = ("name",)
    ordering = ("-created_at",)


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "slug", "created_at")
    search_fields = ("name",)


@admin.register(SizeGuide)
class SizeGuideAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SizeGuide.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
