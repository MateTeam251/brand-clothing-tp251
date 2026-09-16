from django.contrib import admin

from products.models import (ProductType,
                             Product,
                             ProductColor,
                             ProductImage,
                             Color,
                             SizeGuide,
                             Collection)


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ("name", "hex_code")
    search_fields = ("name",)


@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ("product", "color", "is_available")
    list_filter = ("is_available", "color")
    search_fields = ("product__name", "color__name")


admin.site.register(ProductImage)
admin.site.register(ProductType)


class ProductColorInline(admin.TabularInline):
    model = ProductColor
    extra = 1
    autocomplete_fields = ["color"]


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "price_uah", "is_available", "is_bestseller")
    inlines = [ProductColorInline, ProductImageInline]


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "slug", "created_at")


@admin.register(SizeGuide)
class SizeGuideAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SizeGuide.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
