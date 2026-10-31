from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from core.enums import Currency, Size, DeliveryProvider, OrderStatus
from core.pricing import calc_discounted
from products.models import Product
from carts.models import Cart


class Order(models.Model):
    """
    Customer order.

    The order stores a snapshot of the customer and financial data at the time of purchase.
    This prevents data from previous orders from being changed when updating the customer profile or product data.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )

    first_name = models.CharField(
        max_length=255,
    )

    last_name = models.CharField(
        max_length=255,
    )

    user_phone = models.CharField(
        max_length=50,
    )

    email = models.EmailField()

    status = models.CharField(
        max_length=45,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING
    )

    currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    delivery_provider = models.CharField(
        max_length=30,
        choices=DeliveryProvider.choices,
    )

    delivery_address = models.TextField(
        help_text="Final delivery address at the time of order placement.",
    )

    delivery_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Provider specific delivery data.",
    )

    cart = models.ForeignKey(
        Cart,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        help_text="The cart from which this order was created.",
    )

    order_reference = models.CharField(
        max_length=32,
        unique=True,
        null=True,
        blank=True,
        editable=False,
        help_text="Public order number shown to customers and support.",
    )

    admin_comment = models.TextField(
        blank=True,
        help_text="Internal staff note. Never shown to customers.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["status", "-created_at"],
                name="order_status_created_idx"
            ),
            models.Index(
                fields=["user", "-created_at"],
                name="order_user_created_idx"
            )
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(delivery_address__isnull=False) & ~models.Q(delivery_address="") &
                    models.Q(email__isnull=False) & ~models.Q(email="") &
                    models.Q(first_name__isnull=False) & ~models.Q(first_name="") &
                    models.Q(last_name__isnull=False) & ~models.Q(last_name="") &
                    models.Q(user_phone__isnull=False) & ~models.Q(user_phone="")
                ),
                name="order_fields_must_be_filled",
            )
        ]

    def __str__(self):
        return self.order_reference or f"Order #{self.pk}"


class OrderItem(models.Model):
    """
    Product snapshot included in an order.
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="order_items",
    )

    product_name = models.CharField(
        max_length=255,
    )

    product_main_image = models.CharField(
        max_length=500,
        blank=True,
        help_text="URL or path to the product main image at the time of purchase.",
    )

    size = models.CharField(
        max_length=10,
        choices=Size.choices,
    )

    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
    )

    fabric_composition_ua = models.CharField(
        max_length=255,
        blank=True,
    )

    fabric_composition_eng = models.CharField(
        max_length=255,
        blank=True,
    )

    price_at_purchase = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    discount_percent_at_purchase = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(discount_percent_at_purchase__lte=100)
                ),
                name="order_item_discount_lte_100"
            )
        ]

    @property
    def unit_price_after_discount(self) -> str:
        """
        Price per 1 unit after applying discount.
        """

        return calc_discounted(
            self.price_at_purchase,
            self.discount_percent_at_purchase,
        )

    @property
    def line_subtotal(self) -> Decimal:
        """
        Total subtotal amount without discount for this order item.
        """

        return self.price_at_purchase * self.quantity

    @property
    def line_total(self) -> Decimal:
        """
        Final total amount after discount for this order item.
        """

        # unit_price_after_discount is a str ("900.00"): str * int would repeat it.
        return Decimal(self.unit_price_after_discount) * self.quantity

    def __str__(self):
        return f"{self.product_name} - {self.size} x {self.quantity}"
