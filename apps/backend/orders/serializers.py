from rest_framework import serializers

from orders.models import OrderItem, Order
from core.enums import Currency, DeliveryProvider


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for products included in a customer order.

    The "Product" and "Financial Data" fields are snapshots of the product state
    stored at the time of order creation and cannot be modified via the client API.
    """

    unit_price_after_discount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )

    line_subtotal = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )

    line_total = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = OrderItem
        fields = (
            "id",
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
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    """
    Customer facing order serializer.

    All fields are read-only as customers should not be able to create,
    modify, cancel or adjust financial details/order status through this API.
    """

    items = OrderItemSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Order
        fields = (
            "id",
            "user_name",
            "user_phone",
            "email",
            "delivery_address",
            "created_at",
            "status",
            "currency",
            "subtotal",
            "discount_amount",
            "total_amount",
            "delivery_provider",
            "delivery_data",
            "items",
        )
        read_only_fields = fields


class CheckoutSerializer(serializers.ModelSerializer):
    """
    Validates the customer data required to create an order from the current cart.

    The serializer only validates the data input. The order total, prices, discounts,
    and other financial indicators are calculated by the checkout service,
    based on the current cart and product data.
    """

    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    phone = serializers.CharField(max_length=50)
    email = serializers.EmailField()

    currency = serializers.ChoiceField(
        choices=Currency.choices,
    )

    delivery_provider = serializers.ChoiceField(
        choices=DeliveryProvider.choices,
    )

    delivery_address = serializers.CharField(
        max_length=255,
        required=True,
    )

    delivery_data = serializers.JSONField(
        read_only=False,
        default=dict,
        help_text="Delivery service details (city, branch, postal code, etc.)",
    )

    class Meta:
        model = Order
        fields = (
            "first_name",
            "last_name",
            "phone",
            "email",
            "currency",
            "delivery_provider",
            "delivery_address",
            "delivery_data",
        )


class CheckoutResponseSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(required=False)
    payment_id = serializers.IntegerField()
    payment_url = serializers.URLField()
