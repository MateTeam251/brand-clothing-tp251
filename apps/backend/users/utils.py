from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.core.mail import EmailMessage
from urllib.parse import urlencode
from django.conf import settings

from users.tokens import account_activation_token

def send_activation_email(request, user):
    """
    Send an account activation email to a newly registered user.

    Builds a uid/token-based activation link (using a custom token
    generator, ``account_activation_token``) pointing to the
    "users:activate" URL, renders it into an HTML email template, and
    sends it to the user's email address.

    Args:
        request (HttpRequest): The current request, used to build an
            absolute URL (scheme + host) for the activation link.
        user (User): The user to activate. Must have a valid ``pk`` and
            ``email``.

    Returns:
        None

    Side effects:
        Sends an HTML email via ``EmailMessage.send()``. Errors raised by
        the email backend (e.g. connection issues) are not caught here
        and will propagate to the caller.

    Related:
        The generated uid/token pair is expected to be verified by the
        "users:activate" view, which should mark the user as
        ``is_active=True`` on success.
    """
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_activation_token.make_token(user)

    activation_path = reverse("users:activate", kwargs={"uidb64": uid, "token": token})
    activation_link = request.build_absolute_uri(activation_path)

    subject = "Activate your account"
    message = render_to_string("users/activation_email.html", {
        "user": user,
        "activation_link": activation_link,
    })
    email = EmailMessage(subject, message, to=[user.email])
    email.content_subtype = "html"
    email.send()


def send_password_reset_link(request, user):
    """
    Send a password reset email to an existing user.

    Builds a uid/token-based reset link using Django's built-in
    ``default_token_generator`` (the same mechanism used by Django's
    default password reset flow), pointing to the frontend page
    ``{FRONTEND_URL}/resetpassword?uid=<uid>&token=<token>``, renders
    it into an HTML email template, and sends it to the user's email
    address.

    Args:
        request (HttpRequest): The current request. Not used to build
            the link (it points to ``settings.FRONTEND_URL``); kept for
            a consistent signature with ``send_activation_email``.
        user (User): The user requesting a password reset. Must have a
            valid ``pk`` and ``email``.

    Returns:
        None

    Side effects:
        Sends an HTML email via ``EmailMessage.send()``. Errors raised by
        the email backend are not caught here and will propagate to the
        caller.

    Related:
        The frontend reads ``uid`` and ``token`` from the query string
        and sends them to the "users:password_reset_confirm" endpoint,
        where they are verified by
        ``PasswordResetConfirmSerializer.validate`` (checked against
        ``default_token_generator.check_token``) before the password is
        actually changed.
    """
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    query = urlencode({"uid": uid, "token": token})
    reset_link = f"{settings.FRONTEND_URL}/resetpassword?{query}"

    subject = "Password Reset"
    message = render_to_string("users/password_reset.html", {
        "user": user,
        "reset_link": reset_link,
    })
    email = EmailMessage(subject, message, to=[user.email])
    email.content_subtype = "html"
    email.send()

def send_email_change_confirmation(request, user, new_email, token):
    """
    Send a confirmation link for an email change to the new address.

    The link points to the "users:email_change_confirm" backend URL,
    which applies the change and redirects to the frontend.

    Args:
        request (HttpRequest): The current request, used to build an
            absolute URL (scheme + host) for the confirmation link.
        user (User): The user requesting the change. Its ``email`` is
            still the old one at this point.
        new_email (str): The address to confirm. The email is sent here,
            not to ``user.email``.
        token (str): Signed token from ``make_email_change_token``.

    Returns:
        None

    Side effects:
        Sends an HTML email via ``EmailMessage.send()``. Errors raised by
        the email backend are not caught here and will propagate to the
        caller.
    """
    confirm_path = reverse("users:email_change_confirm", kwargs={"token": token})
    confirm_link = request.build_absolute_uri(confirm_path)

    subject = "Confirm your new email"
    message = render_to_string("users/email_change_confirm.html", {
        "user": user,
        "new_email": new_email,
        "confirm_link": confirm_link,
    })
    email = EmailMessage(subject, message, to=[new_email])
    email.content_subtype = "html"
    email.send()


def send_email_change_notification(user, old_email):
    """
    Notify the old address that the account email has been changed.

    Sent after the change is confirmed, so the real owner learns about it
    if someone else changed the email.

    Args:
        user (User): The user whose email was changed. ``user.email`` is
            already the new address.
        old_email (str): The previous address. The email is sent here.

    Returns:
        None

    Side effects:
        Sends an HTML email via ``EmailMessage.send()``. Errors raised by
        the email backend are not caught here and will propagate to the
        caller.
    """
    subject = "Your email was changed"
    message = render_to_string("users/email_change_notification.html", {
        "user": user,
        "old_email": old_email,
    })
    email = EmailMessage(subject, message, to=[old_email])
    email.content_subtype = "html"
    email.send()
