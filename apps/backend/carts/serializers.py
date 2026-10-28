from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from decimal import Decimal, ROUND_HALF_UP
from core.mixins import CurrencyMixin, LanguageMixin

from carts.models import CartItem, Cart
from products.serializers import ProductImageSerializer
from core.pricing import calc_discounted, get_discounted_price


class CartItemSerializer(CurrencyMixin, serializers.ModelSerializer):
    """
    Read-only representation of a cart line item for GET /api/cart/.
    Mirrors ProductListSerializer's price logic (discount-aware),
    but scoped to a single unit price and a line total (unit * quantity).
    """
    name = serializers.CharField(source="product.name", read_only=True, help_text="Product name.")
    main_image = serializers.SerializerMethodField(help_text="Main photo of the product, or null.")
    price = serializers.SerializerMethodField(  # price for 1 product
        help_text="Price of ONE item after discount, in the `?currency=` currency, e.g. \"900.00\".")
    total_price = serializers.SerializerMethodField(  # price * quantity - price for THIS item considering quantity of items in cart. NOT the total price for cart
        help_text="`price` × `quantity` for this line (not the whole cart).")
    is_available = serializers.BooleanField(
        source="product.is_available", read_only=True,
        help_text="false = the product went out of stock after it was added. Such a line can only be "
                  "reduced or deleted, and the order can't be placed until it is removed.")
    is_archived = serializers.BooleanField(
        source="product.is_archived", read_only=True,
        help_text="true = the product became archived after it was added to the cart. Such a line can only "
                  "be reduced or deleted, and the order can't be placed until it is removed."
    )

    class Meta:
        model = CartItem
        fields = ("id", "product", "name", "main_image", "size", "quantity", "price", "total_price", "is_available", "is_archived")
        read_only_fields = fields
        extra_kwargs = {
            "id": {"help_text": "Cart line id; use it in `/api/cart/items/{id}/`."},
            "product": {"help_text": "Product id."},
            "size": {"help_text": "Selected size."},
            "quantity": {"help_text": "Number of items of this product and size."},
        }

    @extend_schema_field(ProductImageSerializer(allow_null=True))
    def get_main_image(self, obj):
        first_image = obj.product.images.first()
        if first_image:
            return ProductImageSerializer(first_image, context=self.context).data
        return None

    def _unit_price(self, obj) -> str:
        currency = self._currency()
        product = obj.product
        if product.discount_percent:
            return calc_discounted(
                product.price_usd if currency == "usd" else product.price_uah,
                product.discount_percent,
            )
        base = product.price_usd if currency == "usd" else product.price_uah
        return str(base)

    def get_price(self, obj) -> str:
        return self._unit_price(obj)

    def get_total_price(self, obj) -> str:
        return str(Decimal(self._unit_price(obj)) * obj.quantity)


class CartItemWriteSerializer(serializers.ModelSerializer):
    """
    Used for POST /api/cart/items/ (add to cart) and
    PATCH /api/cart/items/{id}/ (change quantity/size).
    Client sends only product+size+quantity — price is never accepted
    from the client, it's always derived server-side (see CartItemSerializer).
    """
    quantity = serializers.IntegerField(
        default=1, min_value=1,
        help_text="Number of items, 1 or more. POST: default 1, and it is ADDED to the quantity already in "
                  "the cart for the same product and size. PATCH: the new quantity.")
    class Meta:
        model = CartItem
        fields = ("id", "product", "quantity", "size")
        read_only_fields = ("id",)
        extra_kwargs = {
            "product": {"help_text": "Product id. Must have `is_available: true` and not be archived, otherwise 400."},
            "size": {"help_text": "Size. The same product in two sizes makes two cart lines."},
        }

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value

    def validate(self, attrs):
        current = self.instance.product if self.instance else None
        product = attrs.get("product", current)
        adding = (
            self.instance is None
            or product != current
            or attrs.get("size", self.instance.size) != self.instance.size
            or attrs.get("quantity", 0) > self.instance.quantity
        )
        if (not product.is_available or product.is_archived) and adding:
            raise serializers.ValidationError({"product": "This product is not available."})
        return attrs

    def create(self, validated_data):
        cart = self.context["cart"]
        product = validated_data["product"]
        size = validated_data["size"]
        quantity = validated_data["quantity"]

        item, created = CartItem.objects.get_or_create(
            cart=cart, product=product, size=size,
            defaults={"quantity": quantity},
        )
        if not created:
            item.quantity += quantity
            item.save(update_fields=["quantity"])
        return item



class CartSerializer(CurrencyMixin, serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True, help_text="Cart lines (product + size).")
    items_count = serializers.SerializerMethodField(  # "Items(2)" - sum of quantity
        help_text="Total number of items: sum of `quantity` over all lines.")
    items_total = serializers.SerializerMethodField(  # "total price" — sum of total_price per item
        help_text="Sum of `total_price` of all lines, in the `?currency=` currency. \"0\" for an empty cart.")

    class Meta:
        model = Cart
        fields = ("id", "status", "items", "items_count", "items_total")
        extra_kwargs = {
            "id": {"help_text": "Cart id."},
            "status": {"help_text": "Always `active` here: this endpoint returns only the current cart."},
        }

    def get_items_count(self, obj) -> int:
        return sum(item.quantity for item in obj.items.all())

    def get_items_total(self, obj) -> str:
        total = sum(
            Decimal(CartItemSerializer(item, context=self.context).get_total_price(item))
            for item in obj.items.all()
        )
        return str(total)
