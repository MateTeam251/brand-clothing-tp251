from django.conf import settings
from django.core.mail import send_mail


def send_availability_request_notification(request_obj):
    """
    Notifies the store manager by email that someone wants to know
    whether a product is available. Fire-and-forget — a failed email
    should not break the API response for the person submitting the form.
    """
    subject = f"Запит наявності: {request_obj.product.name}"
    message = (
        f"Товар: {request_obj.product.name}\n"
        f"Лінк: http://127.0.0.1:8000/api/products/{request_obj.product.id}\n"
        f"Ім'я: {request_obj.name}\n"
        f"Телефон: {request_obj.phone_number}\n"

    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [settings.MANAGER_NOTIFICATION_EMAIL],
        fail_silently=True,
    )
