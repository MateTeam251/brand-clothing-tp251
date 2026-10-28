from django.db import models


class Currency(models.TextChoices):
    UAH = "UAH", "UAH"
    USD = "USD", "USD"


class Size(models.TextChoices):
    XXS = "2XS", "2XS"
    XS = "XS", "XS"
    S = "S", "S"
    M = "M", "M"
    L = "L", "L"
    XL = "XL", "XL"
    XXL = "2XL", "2XL"
    XXXL = "3XL", "3XL"
    XXXXL = "4XL", "4XL"


class DeliveryProvider(models.TextChoices):
    NOVA_POSHTA = "NOVA_POSHTA", "Nova Poshta"

class DeliveryType(models.TextChoices):
    BRANCH = "branch", "Відділення"
    COURIER = "courier", "Кур'єром"


class AvailabilityRequestStatusEnum(models.TextChoices):
    NEW = "new", "New"
    CONTACTED = "contacted", "Contacted"
    CLOSED = "closed", "Closed"


class OrderStatus(models.TextChoices):
    """
    Customer-facing order lifecycle.

    The "PENDING" status is a technical prepayment status used during order placement.
    The final business order begins with the "PAID" status after successful payment.
    """

    PENDING = "PENDING", "Pending"
    PAID = "PAID", "Paid"
    AWAITING_SHIPMENT = "AWAITING_SHIPMENT", "Awaiting Shipment"
    SHIPPED = "SHIPPED", "Shipped"
    DELIVERED = "DELIVERED", "Delivered"
    CANCELED = "CANCELED", "Canceled"


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    SUCCESSFUL = "SUCCESSFUL", "Successful"
    FAILED = "FAILED", "Failed"
    REFUNDED = "REFUNDED", "Refunded"
    DUPLICATE = "DUPLICATE", "Duplicate"


class PaymentProvider(models.TextChoices):
    WAYFORPAY = "WAYFORPAY", "Wayforpay"
