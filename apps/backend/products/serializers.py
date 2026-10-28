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

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from products.models import (Product,
                             ProductImage,
                             SizeGuide,
                             Collection,
                             AvailabilityRequest)
from core.mixins import (CurrencyMixin,
                         LanguageMixin)
from core.pricing import get_discounted_price





class CollectionSerializer(LanguageMixin, serializers.ModelSerializer):
    description = serializers.SerializerMethodField(help_text="Description in the `?lang=` language. Can be empty.")

    class Meta:
        model = Collection
        fields = ("id", "image", "slug", "name", "description")
        extra_kwargs = {
            "image": {"help_text": "Full URL of the cover image, or null if there is none."},
            "slug": {"help_text": "URL name of the collection; used in `/api/products/collections/{slug}/` "
                                  "and in the `?collection=` filter of the product list."},
            "name": {"help_text": "Collection name (not translated)."},
        }


    def get_description(self, obj) -> str:
        """Returns description_eng or description_ua depending on self._lang()."""
        return obj.description_eng if self._lang() == "eng" else obj.description_ua

class CollectionDetailSerializer(CollectionSerializer):
    """Full variant — with ProductList, for a page with a specific page."""
    products = serializers.SerializerMethodField(help_text="All non-archived products of the collection, not paginated.")

    class Meta(CollectionSerializer.Meta):
        fields = CollectionSerializer.Meta.fields + ("products",)

    def get_products(self, obj):  # schema type is set below ProductListSerializer

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
    description = serializers.SerializerMethodField(help_text="Size guide text in the `?lang=` language.")

    class Meta:
        model = SizeGuide
        fields = ("image", "description")
        extra_kwargs = {"image": {"help_text": "Full URL of the size chart image, or null."}}

    def get_description(self, obj) -> str:
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
        extra_kwargs = {
            "image": {"help_text": "Full URL of the photo."},
            "order": {"help_text": "Position in the gallery; `0` is the main photo."},
        }



PRICE_HELP = "Price before discount in the `?currency=` currency, string with 2 decimals, e.g. \"1000.00\"."
DISCOUNTED_PRICE_HELP = ("Price after `discount_percent`, string with 2 decimals; "
                         "null when the product has no discount.")
IS_FAVORITE_HELP = "Whether the logged-in user has this product in favorites. Always false for guests."
PRODUCT_FLAGS_HELP = {
    "name": {"help_text": "Product name (not translated)."},
    "is_available": {"help_text": "In stock. When false the product can't be added to the cart, and the page "
                                  "shows a \"check availability\" form instead (see availability-requests)."},
    "is_bestseller": {"help_text": "Shown in the bestsellers block; filter with `?is_bestseller=true`."},
    "is_new_collection": {"help_text": "\"New collection\" badge on the card."},
}


class ProductListSerializer(LanguageMixin, CurrencyMixin, serializers.ModelSerializer):
    """
    Lightweight serializer for the product list endpoint (GET /api/products/).

    Excludes description, fabric_composition, the full image gallery,
    and the size guide — only what's needed for a catalog card.
    Use ProductDetailSerializer for full product details.
    """
    main_image = serializers.SerializerMethodField(help_text="Main photo (`order` 0), or null if the product has no photos.")
    price = serializers.SerializerMethodField(help_text=PRICE_HELP)
    discounted_price = serializers.SerializerMethodField(help_text=DISCOUNTED_PRICE_HELP)
    collection = serializers.SerializerMethodField(help_text="Collection of the product, or null.")
    is_favorite = serializers.SerializerMethodField(help_text=IS_FAVORITE_HELP)

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
        extra_kwargs = PRODUCT_FLAGS_HELP

    @extend_schema_field(CollectionSerializer(allow_null=True))
    def get_collection(self, obj):
        if obj.collection:
            return CollectionSerializer(obj.collection, context=self.context).data
        return None

    def get_price(self, obj) -> str:
        """Returns the original (non-discounted) price as a string, in the currency from self._currency()."""
        price = obj.price_usd if self._currency() == "usd" else obj.price_uah
        return str(price)

    def get_discounted_price(self, obj) -> str | None:
        """Returns the discounted price as a string, or None if there is no discount."""
        return get_discounted_price(obj, self._currency())


    @extend_schema_field(ProductImageSerializer(allow_null=True))
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

    def get_is_favorite(self, obj) -> bool:
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
    images = ProductImageSerializer(many=True, read_only=True, help_text="All photos, sorted by `order`.")
    type = serializers.SerializerMethodField(help_text="Product type name in the `?lang=` language, e.g. \"Сукня\" / \"Dress\".")
    slug = serializers.SerializerMethodField(help_text="Product type slug")
    description = serializers.SerializerMethodField(help_text="Description in the `?lang=` language. Can be empty.")
    fabric_composition = serializers.SerializerMethodField(help_text="Fabric composition in the `?lang=` language. Can be empty.")
    size_guide = serializers.SerializerMethodField(help_text="The size guide; the same one for every product.")
    price = serializers.SerializerMethodField(help_text=PRICE_HELP)
    discounted_price = serializers.SerializerMethodField(help_text=DISCOUNTED_PRICE_HELP)
    collection = serializers.SerializerMethodField(help_text="Collection of the product, or null.")
    is_favorite = serializers.SerializerMethodField(help_text=IS_FAVORITE_HELP)

    class Meta:
        model = Product
        fields = ("id", "name", "type", "slug", "collection", "description", "fabric_composition",
                  "price", "discounted_price",
                  "is_bestseller", "images", "is_available", "size_guide", "is_favorite")
        extra_kwargs = PRODUCT_FLAGS_HELP

    @extend_schema_field(CollectionSerializer(allow_null=True))
    def get_collection(self, obj):
        if obj.collection:
            return CollectionSerializer(obj.collection, context=self.context).data
        return None

    def get_price(self, obj) -> str:
        """Returns the original (non-discounted) price as a string, in the currency from self._currency()."""
        price = obj.price_usd if self._currency() == "usd" else obj.price_uah

        return str(price)

    def get_type(self, obj) -> str:
        """Returns the product type's name (ProductType) in the language from self._lang()."""
        return obj.type.name_eng if self._lang() == "eng" else obj.type.name_ua

    def get_slug(self, obj):
        return obj.type.slug

    def get_description(self, obj) -> str:
        """Returns the product description in the language from self._lang()."""
        return obj.description_eng if self._lang() == "eng" else obj.description_ua

    def get_fabric_composition(self, obj) -> str:
        """Returns the product's fabric composition in the language from self._lang()."""
        return obj.fabric_composition_eng if self._lang() == "eng" else obj.fabric_composition_ua

    @extend_schema_field(SizeGuideSerializer)
    def get_size_guide(self, obj):
        """
        Returns the size guide which is a singleton in the whole project
        """
        return SizeGuideSerializer(SizeGuide.load(), context=self.context).data

    def get_discounted_price(self, obj) -> str | None:
        """Returns the discounted price as a string, or None if there is no discount."""
        return get_discounted_price(obj, self._currency())

    def get_is_favorite(self, obj) -> bool:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.favorited_by.filter(user=request.user).exists()



# ProductListSerializer is defined after CollectionDetailSerializer, so its type is attached here.
extend_schema_field(ProductListSerializer(many=True))(CollectionDetailSerializer.get_products)


class AvailabilityRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailabilityRequest
        fields = ("product", "name", "phone_number")
        extra_kwargs = {
            "product": {"help_text": "Product id. Must be a product with `is_available: false` "
                                       "that is not archived, otherwise 400."},
            "name": {"help_text": "Name of the person to call back, up to 100 characters."},
            "phone_number": {"help_text": "Phone to call back, up to 20 characters. Format is not checked."},
        }


    def validate_product(self, product):
        if product.is_available:
            raise serializers.ValidationError("This product is already available.")
        elif product.is_archived:
            raise serializers.ValidationError("This product is archived")
        return product
