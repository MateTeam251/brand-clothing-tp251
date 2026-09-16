"""
Serializers for the Product API.

Supported query parameters (used with /api/products/ and /api/products/{id}/):

    ?lang=en | ?lang=ua        — language for translatable fields (product type name,
                                  description, fabric_composition, size_guide.description).
                                  Default: "ua". Any value other than "en"
                                  (including a missing parameter) is treated as Ukrainian.

    ?currency=usd | ?currency=uah — currency for price/discounted_price.
                                     Default: "uah". Any value other than "usd"
                                     is treated as Ukrainian hryvnia.

Language and currency are independent parameters and can be combined in any order:
    /api/products/1/?lang=en&currency=usd

Monetary fields (price, discounted_price) are always returned as STRINGS
with two decimal places (e.g. "1000.00"), not as numbers — this avoids
precision loss when parsed on the frontend and keeps them consistent
with regular DecimalField output.

If a product has no discount (discount_percent == 0), discounted_price
returns null instead of duplicating price.
"""

from rest_framework import serializers
from products.models import (Product,
                             ProductImage,
                             SizeGuide,
                             Collection)
from core.mixins import CurrencyMixin, LanguageMixin
from core.pricing import get_discounted_price





class CollectionSerializer(LanguageMixin, serializers.ModelSerializer):
    description = serializers.SerializerMethodField()

    class Meta:
        model = Collection
        fields = ("id", "slug", "name", "description")


    def get_description(self, obj):
        """Returns description_eng or description_ua depending on self._lang()."""
        return obj.description_eng if self._lang() == "eng" else obj.description_ua

class CollectionDetailSerializer(CollectionSerializer):
    """Full variant — with ProductList, for a page with a specific page."""
    products = serializers.SerializerMethodField()

    class Meta(CollectionSerializer.Meta):
        fields = CollectionSerializer.Meta.fields + ("products",)

    def get_products(self, obj):
        products = obj.products.all()
        return ProductListSerializer(products, many=True, context=self.context).data


class SizeGuideSerializer(LanguageMixin, serializers.ModelSerializer):
    """
    Serializes a SizeGuide, which is attached to a product type.

    The description field is automatically picked based on the request
    language (description_ua / description_eng on the model).

    Used as a nested serializer inside ProductDetailSerializer —
    not exposed as a standalone endpoint on its own.
    """
    description = serializers.SerializerMethodField()

    class Meta:
        model = SizeGuide
        fields = ("image", "description")

    def get_description(self, obj):
        """Returns description_eng or description_ua depending on self._lang()."""
        return obj.description_eng if self._lang() == "eng" else obj.description_ua


class ProductImageSerializer(serializers.ModelSerializer):
    """
    Serializes a single product image.

    order = 0 marks the main image (see the unique_main_image_per_product
    constraint on the ProductImage model).

    color is the id of the related color and can be null if the image
    isn't tied to a specific color (a generic product photo).
    """
    class Meta:
        model = ProductImage
        fields = ("id", "image", "order")



class ProductListSerializer(LanguageMixin, CurrencyMixin, serializers.ModelSerializer):
    """
    Lightweight serializer for the product list endpoint (GET /api/products/).

    Excludes description, fabric_composition, the full image gallery,
    and the size guide — only what's needed for a catalog card.
    Use ProductDetailSerializer for full product details.
    """
    main_image = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    discounted_price = serializers.SerializerMethodField()
    collection = serializers.SerializerMethodField()
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ("id",
                  "name",
                  "collection",
                  "main_image",
                  "price",
                  "discounted_price",
                  "is_available",
                  "is_bestseller",
                  "is_new_collection",
                  "is_favorite"
                  )

    def get_collection(self, obj):
        if obj.collection:
            return CollectionSerializer(obj.collection, context=self.context).data
        return None

    def get_price(self, obj):
        """Returns the original (non-discounted) price as a string, in the currency from self._currency()."""
        price = obj.price_usd if self._currency() == "usd" else obj.price_uah
        return str(price)

    def get_discounted_price(self, obj):
        """Returns the discounted price as a string, or None if there is no discount."""
        return get_discounted_price(obj, self._currency())


    def get_main_image(self, obj):
        """
        Returns the product's first image (order=0, the main image),
        or None if the product has no images at all.
        Relies on Meta.ordering = ["order"] on the ProductImage model.
        """
        first_image = obj.images.first() #we have ordering so it's gonna be an image with order = 0
        if first_image:
            return ProductImageSerializer(first_image, context=self.context).data
        return None

    def get_is_favorite(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.favorited_by.filter(user=request.user).exists()


class ProductDetailSerializer(LanguageMixin, CurrencyMixin, serializers.ModelSerializer):
    """
    Full serializer for a single product's detail page (GET /api/products/{id}/).

    Unlike ProductListSerializer, this includes the full description,
    fabric composition, the entire image gallery, the list of available
    colors, and the size guide.
    """
    images = ProductImageSerializer(many=True, read_only=True)
    type = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    fabric_composition = serializers.SerializerMethodField()
    size_guide = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    discounted_price = serializers.SerializerMethodField()
    collection = serializers.SerializerMethodField()
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ("id", "name", "type", "collection", "description", "fabric_composition",
                  "price", "discounted_price",
                  "is_bestseller", "images", "is_available", "size_guide", "is_favorite")

    def get_collection(self, obj):
        if obj.collection:
            return CollectionSerializer(obj.collection, context=self.context).data
        return None

    def get_price(self, obj):
        """Returns the original (non-discounted) price as a string, in the currency from self._currency()."""
        price = obj.price_usd if self._currency() == "usd" else obj.price_uah

        return str(price)

    def get_type(self, obj):
        """Returns the product type's name (ProductType) in the language from self._lang()."""
        return obj.type.name_eng if self._lang() == "eng" else obj.type.name_ua

    def get_description(self, obj):
        """Returns the product description in the language from self._lang()."""
        return obj.description_eng if self._lang() == "eng" else obj.description_ua

    def get_fabric_composition(self, obj):
        """Returns the product's fabric composition in the language from self._lang()."""
        return obj.fabric_composition_eng if self._lang() == "eng" else obj.fabric_composition_ua

    def get_size_guide(self, obj):
        """
        Returns the size guide which is a singleton in the whole project
        """
        return SizeGuideSerializer(SizeGuide.load(), context=self.context).data

    def get_discounted_price(self, obj):
        """Returns the discounted price as a string, or None if there is no discount."""
        return get_discounted_price(obj, self._currency())

    def get_is_favorite(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.favorited_by.filter(user=request.user).exists()
