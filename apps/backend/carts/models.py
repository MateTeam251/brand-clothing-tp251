from django.db import models
from django.conf import settings
from products.models import Product
from core.enums import Size
from time import timezone


class CartStatusEnum(models.TextChoices):
    ACTIVE = "active", "Active"
    ABANDONED = "abandoned", "Abandoned"
    CONVERTED = "converted", "Converted"

class Cart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="carts",
    ) #should be null for guest users

    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)

    status = models.CharField(max_length=20,
                              choices=CartStatusEnum.choices,
                              default=CartStatusEnum.ACTIVE)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    abandoned_at = models.DateTimeField(null=True, blank=True)

    abandoned_value_usd = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    abandoned_value_uah = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    converted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user"], condition=models.Q(status=CartStatusEnum.ACTIVE),
                name="unique_active_cart_per_user",
            ),
            models.UniqueConstraint(
                fields=["session_key"], condition=models.Q(status=CartStatusEnum.ACTIVE),
                name="unique_active_cart_per_session",
            ),
        ]
        indexes = [
            models.Index(fields=["status", "updated_at"]) #for future celery tasks
        ]

    def mark_converted(self):
        """
        Call this when an order is successfully placed from this cart.
        Encapsulates everything that "conversion" means, so the Order
        app doesn't need to know Cart's internals.
        """
        self.status = CartStatusEnum.CONVERTED
        self.converted_at = timezone.now()
        self.save(update_fields=["status", "converted_at"])

    def __str__(self):
        return f"Cart #{self.pk} ({self.status})"






class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="cart_items")
    quantity = models.PositiveIntegerField(default=1)
    size = models.CharField(max_length=10, choices=Size.choices)

    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["cart", "product", "size"], name="unique_cart_product_size"),
            models.CheckConstraint(condition=models.Q(quantity__gte=1), name="cartitem_quantity_gte_1")
        ]

    def __str__(self):
        return f"{self.product.name} x{self.quantity} ({self.size})"

