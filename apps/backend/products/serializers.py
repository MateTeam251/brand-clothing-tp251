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
from decimal import Decimal, ROUND_HALF_UP
from products.models import (Product,
                             ProductImage,
                             Color,
                             ProductColor,
                             SizeGuide,
                             Collection)


class LanguageMixin:
    """
    Gives a serializer the _lang() method for resolving the response
    language based on the ?lang= query parameter of the current request.

    Usage: inherit this mixin BEFORE serializers.ModelSerializer and call
    self._lang() inside get_<field>() methods that return translatable content.
    """
    def _lang(self):
        """
        Returns "eng" if the request explicitly passes ?lang=en.
        In all other cases (missing parameter, any other value)
        returns "ua" — Ukrainian is the default language.
        """
        request = self.context.get("request")
        lang = request.GET.get("lang", "ua") if request else "ua"
        return "eng" if lang == "en" else "ua"


class CurrencyMixin:
    """
    Gives a serializer the _currency() method for resolving the response
    currency based on the ?currency= query parameter of the current request.

    Usage: same as LanguageMixin — inherit before serializers.ModelSerializer
    and call self._currency() in methods that deal with price.
    """
    def _currency(self):
        """
        Returns "usd" if the request explicitly passes ?currency=usd.
        In all other cases returns "uah" — hryvnia is the default currency.
        """
        request = self.context.get("request")
        currency = request.GET.get("currency", "uah") if request else "uah"
        return "usd" if currency == "usd" else "uah"

def _calc_discounted(price, discount_percent):
    """
    Calculates the discounted price using Decimal arithmetic throughout
    (no float), to avoid rounding-precision errors.

    :param price: Decimal — the original price in the relevant currency.
    :param discount_percent: int — discount size in percent (0-100).
    :return: str — the discounted price, rounded to 2 decimal places
             (ROUND_HALF_UP), returned as a string, e.g. "900.00".
    """
    multiplier = Decimal(100 - discount_percent) / Decimal(100)
    discounted = price * multiplier
    return str(discounted.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _get_discounted_price(obj, currency):
    """
    Returns the product's discounted price in the given currency,
    or None if the product has no discount (discount_percent == 0).

    :param obj: Product — the product instance.
    :param currency: str — "usd" or "uah", determines which price field
                     (price_usd/price_uah) is used as the base.
    :return: str | None
    """
    if not obj.discount_percent:
        return None
    price = obj.price_usd if currency == "usd" else obj.price_uah
    return _calc_discounted(price, obj.discount_percent)

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
    color = serializers.SerializerMethodField()
    class Meta:
        model = ProductImage
        fields = ("id", "image", "order", "color")

    def get_color(self, obj):
        if obj.color:
            return ColorSerializer(obj.color, context=self.context).data
        return None


class ColorSerializer(serializers.ModelSerializer):
    """Serializes the Color reference model. Color names are always in English."""
    class Meta:
        model = Color
        fields = ("name", "hex_code")

class ProductColorSerializer(serializers.ModelSerializer):
    """
    Serializes a product-color link (ProductColor) along with the color's
    own details.

    is_available reflects whether THIS specific color is currently
    available for THIS specific product (independent of the product's
    overall is_available flag on Product).
    """
    colors = ColorSerializer(source="color", many=False)
    class Meta:
        model = ProductColor
        fields = ("colors", "is_available")

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
        return _get_discounted_price(obj, self._currency())


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
    available_colors = ProductColorSerializer(source="colors", many=True)
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
                  "is_bestseller", "images", "available_colors", "is_available", "size_guide")

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
        return _get_discounted_price(obj, self._currency())

    def get_is_favorite(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.favorited_by.filter(user=request.user).exists()
