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
    name = serializers.CharField(source="product.name", read_only=True)
    main_image = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()        # price for 1 product
    total_price = serializers.SerializerMethodField()  # price * quantity - price for THIS item considering quantity of items in cart. NOT the total price for cart


    class Meta:
        model = CartItem
        fields = ("id", "product", "name", "main_image", "size", "quantity", "price", "total_price")
        read_only_fields = fields

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

    def get_price(self, obj):
        return self._unit_price(obj)

    def get_total_price(self, obj):
        return str(Decimal(self._unit_price(obj)) * obj.quantity)


class CartItemWriteSerializer(serializers.ModelSerializer):
    """
    Used for POST /api/cart-items/ (add to cart) and
    PATCH /api/cart-items/{id}/ (change quantity/size).
    Client sends only product+size+quantity — price is never accepted
    from the client, it's always derived server-side (see CartItemSerializer).
    """
    quantity = serializers.IntegerField(default=1, min_value=1)
    class Meta:
        model = CartItem
        fields = ("id", "product", "quantity", "size")
        read_only_fields = ("id",)

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value

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
    items = CartItemSerializer(many=True, read_only=True)
    items_count = serializers.SerializerMethodField()   # "Items(2)" - sum of quantity
    items_total = serializers.SerializerMethodField()   # "total price" — sum of total_price per item

    class Meta:
        model = Cart
        fields = ("id", "status", "items", "items_count", "items_total")

    def get_items_count(self, obj):
        return sum(item.quantity for item in obj.items.all())

    def get_items_total(self, obj):
        total = sum(
            Decimal(CartItemSerializer(item, context=self.context).get_total_price(item))
            for item in obj.items.all()
        )
        return str(total)
