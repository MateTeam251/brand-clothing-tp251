import logging
import requests
from datetime import timedelta
from decimal import Decimal

from django.db.models import Max
from django.utils import timezone
from django.db import transaction
from rest_framework.exceptions import ValidationError

from carts.models import CartStatusEnum
from core.enums import Currency, PaymentProvider, PaymentStatus, OrderStatus
from core.pricing import calc_discounted
from orders.email_services import send_order_created_email
from orders.exceptions import PaymentProviderUnavailable
from orders.models import OrderItem, Order
from orders.references import build_order_reference
from payments.models import Payment
from payments.providers.wayforpay.callback import sync_payment_status
from payments.providers.wayforpay.purchase import send_purchase_request


logger = logging.getLogger(__name__)

def get_product_price(product, currency):
    """
    Returns the product price for the selected order currency.

    The product stores separate prices in UAH and USD,
    while the Order stores the currency selected during checkout.
    """

    if currency == Currency.UAH:
        return product.price_uah

    if currency == Currency.USD:
        return product.price_usd

    raise ValidationError(
        {"currency": f"Unsupported currency: {currency}"}
    )


def _create_payment_record(order):
    """
    Creates the next payment attempt for an order.

    Must be called inside a transaction where the order row is locked
    (or the order has just been created) so attempt numbers do not race.
    """

    last_attempt = (
        Payment.objects
        .filter(order=order)
        .aggregate(last=Max("attempt"))["last"]
        or 0
    )
    attempt = last_attempt + 1

    return Payment.objects.create(
        order=order,
        currency=order.currency,
        amount=order.total_amount,
        provider=PaymentProvider.WAYFORPAY,
        status=PaymentStatus.PENDING,
        attempt=attempt,
        provider_order_reference=f"{order.order_reference}-{attempt}",
    )


@transaction.atomic
def create_order_from_cart(*, cart, checkout_data):
    """
    Create an order and its initial payment from the current cart.

    Financial values are calculated on the backend based on current Product data.
    The frontend should not provide subtotals, discounts, or total values.
    """

    if cart is None or cart.status != CartStatusEnum.ACTIVE:
        raise ValidationError(
            {"cart": "Cart was not found."}
        )

    cart_items = list(cart.items.select_related("product").all())

    if not cart_items:
        raise ValidationError(
            {"cart": "Cart is empty."}
        )

    currency = checkout_data["currency"]

    subtotal = Decimal("0.00")
    total_amount = Decimal("0.00")

    order_items = []

    for cart_item in cart_items:
        product = cart_item.product

        main_image_obj = product.images.filter(order=0).first()

        image_path = main_image_obj.image.name if main_image_obj and main_image_obj.image else ""

        if not product.is_available:
            raise ValidationError(
                {
                    "cart": f"Product {product.name} is no longer available."
                }
            )

        price = Decimal(str(get_product_price(product, currency)))
        discount_percent = int(product.discount_percent or 0)

        unit_price_after_discount = calc_discounted(
            price,
            discount_percent,
        )

        line_subtotal = price * cart_item.quantity
        line_total = Decimal(unit_price_after_discount) * cart_item.quantity

        subtotal += line_subtotal
        total_amount += line_total

        order_items.append(
            OrderItem(
                product=product,
                product_name=product.name,
                product_main_image=image_path,
                size=cart_item.size,
                quantity=cart_item.quantity,
                fabric_composition_ua=product.fabric_composition_ua,
                fabric_composition_eng=product.fabric_composition_eng,
                price_at_purchase=price,
                discount_percent_at_purchase=discount_percent,
            )
        )

    discount_amount = subtotal - total_amount

    user = cart.user if cart.user and cart.user.is_authenticated else None

    delivery_data = checkout_data.get("delivery_data", {})
    delivery_address = checkout_data.get("delivery_address")

    order = Order.objects.create(
        user=user,
        first_name=checkout_data["first_name"],
        last_name=checkout_data["last_name"],
        user_phone=checkout_data["phone"],
        email=checkout_data["email"],
        status=OrderStatus.PENDING,
        currency=currency,
        subtotal=subtotal,
        discount_amount=discount_amount,
        total_amount=total_amount,
        delivery_provider=checkout_data["delivery_provider"],
        delivery_address=delivery_address,
        delivery_data=delivery_data,
        cart=cart,
    )

    order.order_reference = build_order_reference(order.pk)
    order.save(update_fields=["order_reference"])

    for order_item in order_items:
        order_item.order = order

    OrderItem.objects.bulk_create(order_items)

    payment = _create_payment_record(order)

    transaction.on_commit(lambda: send_order_created_email(order), robust=True)

    return order, payment


def start_payment(*, order, payment):
    """
    Starts a WayForPay payment for the given payment attempt.
    """

    items = list(order.items.all())

    product_names = [item.product_name for item in items]
    product_counts = [str(item.quantity) for item in items]
    product_prices = [str(item.unit_price_after_discount) for item in items]

    try:
        payment_url = send_purchase_request(
            order_reference=str(payment.provider_order_reference),
            order_date=int(payment.created_at.timestamp()),
            amount=str(payment.amount),
            currency=payment.currency,
            product_names=product_names,
            product_counts=product_counts,
            product_prices=product_prices,
            order_timeout=900,
        )
    except (requests.RequestException, ValueError):
        logger.exception(
            "WayForPay purchase request failed: payment=%s",
            payment.provider_order_reference,
        )
        raise PaymentProviderUnavailable()

    payment.payment_url = payment_url
    payment.save(update_fields=["payment_url", "updated_at"])

    return payment_url


def checkout(*, cart, checkout_data):
    """
    Creates the order and initiates its payment.
    """

    order, payment = create_order_from_cart(
        cart=cart,
        checkout_data=checkout_data,
    )

    payment_url = start_payment(
        order=order,
        payment=payment,
    )

    return order, payment, payment_url


@transaction.atomic
def create_payment_attempt(*, order_id):
    """
    Creates a new pending payment attempt or reuses a
    recent pending payment for an unpaid order.
    """
    try:
        order = Order.objects.select_for_update().get(pk=order_id)
    except Order.DoesNotExist:
        raise ValidationError({"order": "Order not found"})

    if order.status != OrderStatus.PENDING:
        raise ValidationError({"order": "This order cannot be paid (already processed or canceled)."})

    payment_attempt_started_at = timezone.now() - timedelta(minutes=14)
    recent_pending_payment = (
        Payment.objects
        .filter(
            order=order,
            status=PaymentStatus.PENDING,
            created_at__gte=payment_attempt_started_at,
        )
        .exclude(payment_url="")
        .order_by("-created_at")
        .first()
    )

    if recent_pending_payment:
        return order, recent_pending_payment

    payment = _create_payment_record(order)

    return order, payment


def retry_payment(*, order_id):
    """
    Creates a new payment attempt or reuses an active payment
    attempt and starts the WayForPay payment flow.
    """

    started_attempts = (
        Payment.objects
        .filter(order_id=order_id, status=PaymentStatus.PENDING)
        .exclude(payment_url="")
        .order_by("-created_at")[:3]
    )
    for pending in started_attempts:
        sync_payment_status(pending)

    order, payment = create_payment_attempt(order_id=order_id)

    if payment.payment_url:
        return order, payment, payment.payment_url

    payment_url = start_payment(
        order=order,
        payment=payment,
    )

    return order, payment, payment_url
