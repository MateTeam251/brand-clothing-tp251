from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import ValidationError

from core.enums import Currency
from orders.models import OrderItem, Order, OrderStatus
from payments.models import Payment, PaymentProvider, PaymentStatus


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

    raise ValidationError(f"currency '{currency}': Unsupported currency")


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
    discount_amount = Decimal("0.00")

    order_items = []

    for cart_item in cart_items:
        product = cart_item.product

        if not product.is_available:
            raise ValidationError(
                {
                    "cart": f"Product {product.name} is no longer available."
                }
            )

        price = get_product_price(product, currency)

        discount_percent = product.discount_percent

        line_subtotal = price * cart_item.quantity
        line_discount = line_subtotal * Decimal(discount_percent) / Decimal("100")

        subtotal += line_subtotal
        discount_amount += line_discount

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

    # TODO Delivery, change to real delivery_cost price form Delivery model
    delivery_cost = Decimal("0.00")

    total_amount = subtotal - discount_amount + delivery_cost

    user = cart.user

    order = Order.objects.create(
        user=user,
        delivery_address=checkout_data["delivery_address"],
        email=checkout_data["email"],
        status=OrderStatus.CREATED,
        currency=currency,
        subtotal=subtotal,
        discount_amount=discount_amount,
        delivery_cost=delivery_cost,
        total_amount=total_amount,
        delivery_provider=checkout_data["delivery_provider"],
        delivery_data=checkout_data.get("delivery_data", {}),
        user_name=f"{checkout_data["first_name"]} {checkout_data["last_name"]}".strip(),
        user_phone=checkout_data["phone"],
    )

    for order_item in order_items:
        order_item.order = order
        order_item.save()

    payment = Payment.objects.create(
        order=order,
        currency=currency,
        amount=total_amount,
        provider=PaymentProvider.WAYFORPAY,
        status=PaymentStatus.PENDING,
    )

    return order, payment
