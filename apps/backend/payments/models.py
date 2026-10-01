import uuid
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from core.enums import Currency
from orders.models import Order


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    SUCCESSFUL = "SUCCESSFUL", "Successful"
    FAILED = "FAILED", "Failed"
    REFUNDED = "REFUNDED", "Refunded"


class PaymentProvider(models.TextChoices):
    WAYFORPAY = "WAYFORPAY", "Wayforpay"


class Payment(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name="payments",
    )

    currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    provider = models.CharField(
        max_length=45,
        choices=PaymentProvider.choices,
    )

    status = models.CharField(
        max_length=45,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )

    transaction_id = models.CharField(
        max_length=100,
        blank=True,
    )

    payment_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Provider specific non-sensitive payment metadata.",
    )

    provider_order_reference = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["order", "-created_at"],
                name="payment_order_date_idx",
            ),
            models.Index(
                fields=["status", "-created_at"],
                name="payment_status_date_idx",
            ),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=["order"],
                condition=models.Q(status=PaymentStatus.SUCCESSFUL),
                name="unique_successful_payment_per_order",
            )
        ]

    def __str__(self):
        return f"Payment #{self.pk} for Order #{self.order_id}"
