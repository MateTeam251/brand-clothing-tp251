from rest_framework import generics, status
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import Address
from users.serializers import (RegisterSerializer,
                               UserProfileSerializer,
                               PasswordResetConfirmSerializer,
                               PasswordResetRequestSerializer, AddressSerializer)
from users.tokens import account_activation_token
from users.utils import send_activation_email

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    Register a new user account.

    Creates an (inactive) user via ``RegisterSerializer`` and sends an
    activation email right after. Open to anyone (no authentication
    required).
    """
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        """
        Save the new user and trigger the activation email.

        Args:
            serializer (RegisterSerializer): The validated serializer
                instance.

        Side effects:
            Sends an activation email via ``send_activation_email``.
        """
        user = serializer.save()
        send_activation_email(self.request, user)



class ActivateAccountView(APIView):
    """
    Confirm a user's email address via an activation link.

    Expects ``uidb64`` and ``token`` from the activation link generated
    by ``send_activation_email``. Renders an HTML page (success or
    invalid) rather than returning JSON, since this endpoint is meant to
    be opened directly in a browser from the email link.
    """
    permission_classes = [AllowAny]
    renderer_classes = [TemplateHTMLRenderer]

    def get(self, request, uidb64, token):
        """
        Validate the uid/token pair and activate the user if valid.

        Args:
            request (HttpRequest): The current request.
            uidb64 (str): Base64url-encoded user primary key.
            token (str): Activation token to verify against the user.

        Returns:
            Response: Renders "users/activation_success.html" (200) on
            success, or "users/activation_invalid.html" (400) if the
            uid/token is invalid, expired, or does not match a user.

        Notes:
            - Idempotent: if the user is already active, the view still
              renders the success page without re-saving.
            - Decoding/lookup failures (bad uid, non-existent user) are
              caught and treated the same as an invalid token, to avoid
              leaking which failure occurred.
        """
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and account_activation_token.check_token(user, token):
            if not user.is_active:
                user.is_active = True
                user.save(update_fields=["is_active"])
            return Response(template_name="users/activation_success.html")

        return Response(template_name="users/activation_invalid.html", status=400)


class ResendActivationView(APIView):
    """
    Resend the activation email for an inactive account.

    Given an email address, resends the activation link if a matching
    inactive account exists.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Resend the activation email.

        Args:
            request (HttpRequest): Expects ``email`` in ``request.data``.

        Returns:
            Response: Always 200 with a generic message, regardless of
            whether the account exists — this prevents user enumeration
            (an attacker cannot use this endpoint to check which emails
            are registered or already active).

        Notes:
            Only accounts with ``is_active=False`` are matched; already
            active accounts silently receive no email.
        """
        email = request.data.get("email")
        try:
            user = User.objects.get(email=email, is_active=False)
        except User.DoesNotExist:
            return Response({"detail": "If the account exists, email was sent."})
        send_activation_email(request, user)
        return Response({"detail": "If the account exists, email was sent."})


class MeView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update the currently authenticated user's profile.

    GET returns the profile; PUT/PATCH updates it. Uses
    ``UserProfileSerializer``, which keeps ``id`` and ``email``
    read-only. Requires authentication.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        Return the profile of the requesting user.

        Returns:
            User: ``request.user`` — the authenticated user always
            operates on their own profile, never another user's.
        """
        return self.request.user

class AddressView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update the authenticated user's shipping address.

    GET returns the address (or 404 if the user hasn't set one yet).
    PUT/PATCH creates or updates it — since the user may not have an
    address yet (it was optional at registration), get_object() falls
    back to creating an empty Address instance rather than raising 404
    on write attempts.
    """
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        address, _ = Address.objects.get_or_create(user=self.request.user)
        return address

class LogoutView(APIView):
    """
    Log the user out by blacklisting their refresh token.

    Requires authentication (a valid access token) and a valid refresh
    token in the request body. Relies on SimpleJWT's token blacklist app
    to invalidate the refresh token so it can no longer be used to
    obtain new access tokens.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Blacklist the provided refresh token.

        Args:
            request (HttpRequest): Expects ``refresh`` in
                ``request.data`` — the refresh token to invalidate.

        Returns:
            Response:
                - 400 if ``refresh`` is missing from the request body.
                - 400 if the token is invalid, malformed, or already
                  expired/blacklisted.
                - 205 (Reset Content) with an empty body on success.
        """
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response({"detail": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_205_RESET_CONTENT)

class PasswordResetRequestView(APIView):
    """
    Request a password reset link for a given email address.

    Throttled per anonymous client (``AnonRateThrottle``) to reduce the
    risk of abuse (e.g. spamming a user's inbox with reset emails or
    probing for registered emails).
    """
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        """
        Validate the email and trigger a password reset email.

        Args:
            request (HttpRequest): Expects ``email`` in ``request.data``.

        Returns:
            Response: 200 with a generic message regardless of whether
            the account exists, to avoid user enumeration. The actual
            "does the user exist" check and email sending happen inside
            ``PasswordResetRequestSerializer.save``.
        """
        serializer = PasswordResetRequestSerializer(
            data=request.data,
            context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save(request=request)
        return Response(
            {"detail": "If the account exists, email was sent."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    """
    Confirm a password reset using the uid/token from the reset link and
    set a new password.
    """
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        """
        Validate the uid/token pair and set the new password.

        Args:
            request (HttpRequest): Expects ``new_password`` in
                ``request.data``.
            uidb64 (str): Base64url-encoded user primary key, taken from
                the URL.
            token (str): Password reset token, taken from the URL.

        Returns:
            Response: 200 with a success message if the uid/token pair
            is valid and the new password passes validation; otherwise
            ``PasswordResetConfirmSerializer`` raises a validation error
            (handled by DRF's default exception handling, typically
            resulting in a 400 response).
        """
        data = {
            "uid": uidb64,
            "token": token,
            "new_password": request.data.get("new_password"),
        }
        serializer = PasswordResetConfirmSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password changed successfully."}, status=status.HTTP_200_OK)
