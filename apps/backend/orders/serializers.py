from rest_framework import serializers

from orders.models import OrderItem, Order


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for products included in a customer order.
    """

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
            "delivery_cost",
            "total_amount",
            "delivery_provider",
            "delivery_data",
            "items",
        )
        read_only_fields = fields
