from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from core.enums import Currency, PaymentProvider, PaymentStatus
from orders.models import Order


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

    payment_url = models.URLField(
        max_length=500,
        blank=True,
    )

    payment_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Provider specific non-sensitive payment metadata.",
    )

    attempt = models.PositiveSmallIntegerField(default=1)

    provider_order_reference = models.CharField(
        max_length=64,
        unique=True,
        editable=False,
        help_text="Unique reference sent to the payment provider: <order_reference>-<attempt>.",
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
            ),
            models.UniqueConstraint(
                fields=["order", "attempt"],
                name="unique_payment_attempt_per_order",
            )
        ]

    def __str__(self):
        return self.provider_order_reference
