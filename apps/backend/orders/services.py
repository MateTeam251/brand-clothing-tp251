from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import ValidationError

from core.enums import Currency
from orders.email_services import send_order_created_email
from orders.models import OrderItem, Order, OrderStatus
from payments.models import Payment, PaymentProvider, PaymentStatus
from payments.providers.wayforpay.purchase import send_purchase_request


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


@transaction.atomic
def create_order_from_cart(*, cart, checkout_data):
    """
    Create an order and its initial payment from the current cart.

    Financial values are calculated on the backend based on current Product data.
    The frontend should not provide subtotals, discounts, or total values.

    TODO: Cart is not yet implemented.
    This service assumes that the Cart provides:

    - cart.user
    - cart.items.all()
    - CartItem.product
    - CartItem.quantity
    - CartItem.size
    - cart.status

    TODO: Session integration is not yet implemented.
    To checkout without registration, in the final implementation, it will be necessary to determine
    the current cart from a guest session.

    TODO: Delivery cost calculation is temporary.
    """

    if cart is None:
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

        if not product.is_available:
            raise ValidationError(
                {
                    "cart": f"Product {product.name} is no longer available."
                }
            )

        price = Decimal(str(get_product_price(product, currency)))
        discount_percent = int(product.discount_percent or 0)

        if discount_percent > 0:
            discount_factor = Decimal(100 - discount_percent) / Decimal("100")
            unit_price_after_discount = (price * discount_factor).quantize(Decimal("0.01"))
        else:
            unit_price_after_discount = price

        line_subtotal = price * cart_item.quantity
        line_total = unit_price_after_discount * cart_item.quantity

        subtotal += line_subtotal
        total_amount += line_total

        order_items.append(
            OrderItem(
                product=product,
                product_name=product.name,
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
        delivery_address=delivery_address,
        email=checkout_data["email"],
        status=OrderStatus.PENDING,
        currency=currency,
        subtotal=subtotal,
        discount_amount=discount_amount,
        total_amount=total_amount,
        delivery_provider=checkout_data["delivery_provider"],
        delivery_data=delivery_data,
        user_name=f"{checkout_data['first_name']} {checkout_data['last_name']}".strip(),
        user_phone=checkout_data["phone"],
    )

    for order_item in order_items:
        order_item.order = order

    OrderItem.objects.bulk_create(order_items)

    payment = Payment.objects.create(
        order=order,
        currency=currency,
        amount=total_amount,
        provider=PaymentProvider.WAYFORPAY,
        status=PaymentStatus.PENDING,
    )

    send_order_created_email(order)

    return order, payment


def start_payment(*, order, payment):
    """
    Starts a WayForPay payment for the given payment attempt.
    """

    items = list(order.items.all())

    product_names = [item.product_name for item in items]
    product_counts = [str(item.quantity) for item in items]
    product_prices = [str(item.unit_price_after_discount) for item in items]

    return send_purchase_request(
        order_reference=str(payment.provider_order_reference),
        order_date=int(order.created_at.timestamp()),
        amount=str(payment.amount),
        currency=payment.currency,
        product_names=product_names,
        product_counts=product_counts,
        product_prices=product_prices,
    )


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

    cart.items.all().delete()

    return order, payment, payment_url


@transaction.atomic
def create_payment_attempt(*, order_id):
    """
    Creates a new pending payment attempt for an existing pending order.
    """
    try:
        order = Order.objects.select_for_update().get(pk=order_id)
    except Order.DoesNotExist:
        raise ValidationError({"order": "Order not found"})

    if order.status != OrderStatus.PENDING:
        raise ValidationError({"order": "Only pending orders can be paid again."})

    payment = Payment.objects.create(
        order=order,
        currency=order.currency,
        amount=order.total_amount,
        provider=PaymentProvider.WAYFORPAY,
        status=PaymentStatus.PENDING,
    )

    return order, payment


def retry_payment(*, order_id):
    """
    Creates a new payment attempt and starts the WayForPay payment flow.
    """

    order, payment = create_payment_attempt(order_id=order_id)

    payment_url = start_payment(
        order=order,
        payment=payment,
    )

    return order, payment, payment_url
