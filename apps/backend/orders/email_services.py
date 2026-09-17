import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.db import transaction
from django.template.loader import render_to_string

from orders.models import Order, OrderStatus

logger = logging.getLogger(__name__)

def _send_email(*, order: Order, template_name: str, subject: str) -> None:
    """
    Private helper: physically renders and sends the email.
    """

    if not order.email:
        logger.warning("Order #%s has no email address. Skipping.", order.id)
        return

    context = {
        "order": order,
        "items": list(order.items.all()),
        "site_url": getattr(settings, "SITE_URL", "http://127.0.0.1:8000"),
    }

    try:
        html_content = render_to_string(template_name, context)
        email = EmailMessage(
            subject=f"{subject} (Order #{order.id})",
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.email],
        )
        email.content_subtype = "html"
        email.send(fail_silently=False)
        logger.info("Email '%s' sent for Order #%s to %s", subject, order.id, order.email)
    except Exception as e:
        logger.error("Failed to send email '%s' for Order #%s: %s", subject, order.id, str(e), exc_info=True)


def _send_safe(order: Order, template_name: str, subject: str) -> None:
    """
    A universal, secure wrapper.
    If there's an active database transaction, it waits for it to be committed.
    If there's no transaction, it sends it immediately.
    """
    transaction.on_commit(lambda: _send_email(order=order, template_name=template_name, subject=subject))


def send_order_created_email(order: Order) -> None:
    """
    Called when an order is created.
    """
    _send_safe(order, "emails/order_created.html", "Your order has been placed")


def send_order_paid_email(order: Order) -> None:
    """
    Called when an order is paid.
    """
    _send_safe(order, "emails/order_paid.html", "Your order has been paid")


def send_order_status_changed_email(order: Order) -> None:
    """

    """

    status_map = {
        OrderStatus.SHIPPED: ("emails/order_shipped.html", "Your order has been sent."),
        OrderStatus.DELIVERED: ("emails/order_delivered.html", "Your order has been delivered."),
        OrderStatus.CANCELED: ("emails/order_canceled.html", "Your order has been canceled"),
    }

    if order.status in status_map:
        template_name, subject = status_map[order.status]
        _send_safe(order, template_name, subject)
