import logging

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core import signing
from django.db import IntegrityError, transaction
from django.shortcuts import redirect
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.throttling import ScopedRateThrottle

from core.openapi import DETAIL_RESPONSE, THROTTLED, UNAUTHORIZED, VALIDATION_ERROR
from users.serializers import (RegisterSerializer,
                               UserProfileSerializer,
                               PasswordResetConfirmSerializer,
                               PasswordResetRequestSerializer,
                               CustomTokenObtainPairSerializer,
                               LogoutSerializer,
                               ResendActivationSerializer,
                               UpdatePasswordInProfileSerializer,
                               UpdateEmailRequestSerializer)
from users.tokens import account_activation_token, read_email_change_token
from users.utils import (send_activation_email,
                         send_email_change_notification)

logger = logging.getLogger(__name__)

User = get_user_model()

TOKEN_PAIR = inline_serializer("TokenPair", {
    "access": serializers.CharField(help_text="Access token: send as `Authorization: Bearer <access>`."),
    "refresh": serializers.CharField(help_text="Refresh token: for `/api/auth/refresh/` and `/api/auth/logout/`."),
})


@extend_schema(
    tags=["auth"],
    summary="Register a new account",
    description="Creates an **inactive** account and sends an activation link to `email`. "
                "The user cannot log in until they open that link "
                "(locally the email is in MailHog, http://localhost:8025).",
    responses={201: RegisterSerializer, 400: VALIDATION_ERROR},
)
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


@extend_schema(
    tags=["auth"],
    summary="Activate an account (link from the email)",
    description="Opened from the activation email, not called by the frontend. `uidb64` and "
                "`token` are the two last parts of the link. Redirects to "
                "`{FRONTEND_URL}/activation/success` or `{FRONTEND_URL}/activation/failed`. "
                "The link is valid for 24 hours; an expired link redirects to `/activation/failed` "
                "(request a new one via `resend-activation/`). Opening the link for an already "
                "active account redirects to `/activation/success`.",
    responses={
        302: OpenApiResponse(description="Redirect to the frontend success or failed page."),
        429: OpenApiResponse(
            DETAIL_RESPONSE,
            description="Too many requests from this IP (30/hour). JSON instead of a redirect."),
    },
)
class ActivateAccountView(APIView):
    """
    Confirm a user's email address via an activation link.

    Expects ``uidb64`` and ``token`` from the activation link generated
    by ``send_activation_email``. Redirects to the frontend (success or
    failed page) rather than returning JSON, since this endpoint is
    meant to be opened directly in a browser from the email link.
    """
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "activation"


    def get(self, request, uidb64, token):
        """
        Validate the uid/token pair, activate the user if valid and
        redirect to the frontend.

        Args:
            request (HttpRequest): The current request.
            uidb64 (str): Base64url-encoded user primary key.
            token (str): Activation token to verify against the user.

        Returns:
            HttpResponseRedirect: 302 to
            ``{FRONTEND_URL}/activation/success`` on success, or to
            ``{FRONTEND_URL}/activation/failed`` if the uid/token is
            invalid, expired, or does not match a user.

        Notes:
            - An already active user is redirected to the success page
              before the token is checked: the activation token includes
              ``is_active`` in its hash, so it is no longer valid after
              activation.
            - The link expires after ``settings.ACTIVATION_TOKEN_TIMEOUT``
              (24 hours); an expired link redirects to the failed page.
            - Decoding/lookup failures (bad uid, non-existent user) are
              caught and treated the same as an invalid token, to avoid
              leaking which failure occurred.
        """
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and user.is_active:
            return redirect(f"{settings.FRONTEND_URL}/activation/success")

        if user is not None and account_activation_token.check_token(user, token):
            user.is_active = True
            user.save(update_fields=["is_active"])
            return redirect(f"{settings.FRONTEND_URL}/activation/success")


        return redirect(f"{settings.FRONTEND_URL}/activation/failed")


@extend_schema(
    tags=["auth"],
    summary="Resend an activation link to non active account",
    description="Resends the activation link to `email` if an **inactive** account with it exists. "
                "The user cannot log in until they open that link "
                "(locally the email is in MailHog, http://localhost:8025). "
                "Always **200** for any valid email, whether or not it was sent",
    request=ResendActivationSerializer,
    responses={200: DETAIL_RESPONSE, 400: VALIDATION_ERROR, 429: THROTTLED},
)
class ResendActivationView(APIView):
    """
    Resend the activation email for an inactive account.

    Given an email address, resends the activation link if a matching
    inactive account exists.
    """
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "resend_activation"

    def post(self, request):
        """
        Resend the activation email.

        Args:
            request (HttpRequest): Expects ``email`` in ``request.data``.

        Returns:
            Response: Always 200 (Except for validation error. Then it returns 400)
            with a generic message, regardless of whether the account exists
            — this prevents user enumeration
            (an attacker cannot use this endpoint to check which emails
            are registered or already active).

        Notes:
            Only accounts with ``is_active=False`` are matched; already
            active accounts silently receive no email.
        """
        serializer = ResendActivationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        try:
            user = User.objects.get(email=email, is_active=False)
        except User.DoesNotExist:
            return Response({"detail": "If the account exists, email was sent."})
        send_activation_email(request, user)
        return Response({"detail": "If the account exists, email was sent."})


@extend_schema_view(
    get=extend_schema(summary="Get my profile", responses={200: UserProfileSerializer, 401: UNAUTHORIZED}),
    put=extend_schema(
        summary="Replace my profile",
        description="Full update: `instagram` must be sent, other fields not sent are left as they are. "
                    "`id` and `email` cannot be changed here; to change the email use `me/email/`.",
        responses={200: UserProfileSerializer, 400: VALIDATION_ERROR, 401: UNAUTHORIZED},
    ),
    patch=extend_schema(
        summary="Update my profile",
        description="Partial update: send only the fields to change. `id` and `email` cannot be changed here; "
                    "to change the email use `me/email/`.",
        responses={200: UserProfileSerializer, 400: VALIDATION_ERROR, 401: UNAUTHORIZED},
    ),
)
@extend_schema(tags=["profile"])
class MeView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update the currently authenticated user's profile.

    GET returns the profile; PUT/PATCH updates it. Uses
    ``UserProfileSerializer``, which keeps ``id`` and ``email``
    read-only (the email is changed via ``UpdateEmailInProfileView``).
    Requires authentication.
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


@extend_schema(
    tags=["auth"],
    summary="Log in",
    description="Returns a JWT pair. Put `access` into **Authorize**; keep `refresh` for "
                "`/api/auth/refresh/` and `/api/auth/logout/`.\n\n"
                "A wrong password and a not yet activated account give the same 401 "
                "`No active account found with the given credentials`.\n\n"
                "If the request carries a guest `sessionid` cookie, the guest cart is merged into the user's cart.",
    responses={
        200: TOKEN_PAIR,
        400: VALIDATION_ERROR,
        401: OpenApiResponse(DETAIL_RESPONSE, description="Wrong email/password, or the account is not activated."),
    },
)
class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


@extend_schema(
    tags=["auth"],
    summary="Get a new access token",
    description="Exchanges `refresh` for a new `access` **and a new `refresh`**. "
                "The old refresh token is blacklisted, so using it again gives 401 `Token is blacklisted`.",
    responses={
        200: TOKEN_PAIR,
        401: OpenApiResponse(DETAIL_RESPONSE, description="Refresh token is invalid, expired or blacklisted."),
    },
)
class RefreshView(TokenRefreshView):
    pass


@extend_schema(
    tags=["auth"],
    summary="Log out",
    description="Blacklists the given refresh token. Needs both the Bearer access token and `refresh` in the body. "
                "The access token itself keeps working until it expires.",
    request=LogoutSerializer,
    responses={
        205: OpenApiResponse(description="Logged out. Empty body."),
        400: OpenApiResponse(DETAIL_RESPONSE, description="`refresh` is missing, invalid or already blacklisted."),
        401: UNAUTHORIZED,
    },
)
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

@extend_schema(
    tags=["auth"],
    summary="Request a password reset email",
    description="Sends a reset link if an account with this email exists. The link is valid for 1 hour. "
                "The response is the same whether the account exists or not, so it can't be used to check "
                "which emails are registered.",
    request=PasswordResetRequestSerializer,
    responses={
        200: OpenApiResponse(DETAIL_RESPONSE, description="Always, for any valid email."),
        400: VALIDATION_ERROR,
        429: THROTTLED,
    },
)
class PasswordResetRequestView(APIView):
    """
    Request a password reset link for a given email address.

    Throttled per client (``ScopedRateThrottle``, scope
    ``password_reset``) to reduce the risk of abuse (e.g. spamming a
    user's inbox with reset emails or probing for registered emails).
    """
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset"

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


@extend_schema(
    tags=["auth"],
    summary="Set a new password (link from the email)",
    description="`uidb64` and `token` are the two last parts of the reset link from the email. "
                "The link is valid for 1 hour and works once: after the password is changed it becomes "
                "invalid. An expired link gives 400 with the error under `token`; request a new one.",
    request=inline_serializer(
        "NewPassword",
        {"new_password": PasswordResetConfirmSerializer().fields["new_password"]},
    ),
    responses={
        200: OpenApiResponse(DETAIL_RESPONSE, description="Password changed."),
        400: OpenApiResponse(
            description="Weak `new_password`, or a broken link: the error comes under `uid` or `token`."),
    },
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

@extend_schema(
    tags=["auth"],
    summary="Change password from the profile",
    description="For a logged-in user. Requires the current password. "
                "Already issued access/refresh tokens keep working.",
    request=UpdatePasswordInProfileSerializer,
    responses={
        200: OpenApiResponse(DETAIL_RESPONSE, description="Password changed."),
        400: VALIDATION_ERROR,
        401: UNAUTHORIZED,
        429: THROTTLED,
    },
)
class UpdatePasswordInProfileView(APIView):
    """
        Change the authenticated user's password after checking the current one.
        """
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "change_password"

    def post(self, request):
        serializer = UpdatePasswordInProfileSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password changed successfully."}, status=status.HTTP_200_OK)


@extend_schema(
    tags=["profile"],
    summary="Request an email change",
    description="For a logged-in user. Requires the current password. The email is **not** changed yet: "
                "a confirmation link is sent to `new_email` "
                "(locally the email is in MailHog, http://localhost:8025). "
                "The change is applied once the link is opened; it is valid for 24 hours.",
    request=UpdateEmailRequestSerializer,
    responses={
        200: OpenApiResponse(DETAIL_RESPONSE, description="Confirmation link sent to the new email."),
        400: VALIDATION_ERROR,
        401: UNAUTHORIZED,
        429: THROTTLED,
    },
)
class UpdateEmailInProfileView(APIView):
    """
    Start an email change for the authenticated user.

    Checks the password and the new email via
    ``UpdateEmailRequestSerializer`` and sends a confirmation link to
    the new address. The email is changed later by
    ``EmailChangeConfirmView``.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "change_email"

    def post(self, request):
        serializer = UpdateEmailRequestSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Confirmation link sent to the new email."}, status=status.HTTP_200_OK)


@extend_schema(
    tags=["profile"],
    summary="Confirm an email change (link from the email)",
    description="Opened from the confirmation email, not called by the frontend. `token` is the last part "
                "of the link. Changes the account email and redirects to "
                "`{FRONTEND_URL}/email-change/success` or `{FRONTEND_URL}/email-change/failed`. "
                "The link is valid for 24 hours and works once. It also fails if the new email has been "
                "taken by another account meanwhile. On success a notification is sent to the old email.",
    responses={
        302: OpenApiResponse(description="Redirect to the frontend success or failed page."),
        429: OpenApiResponse(
            DETAIL_RESPONSE,
            description="Too many requests from this IP (30/hour). JSON instead of a redirect."),
    },
)
class EmailChangeConfirmView(APIView):
    """
    Apply an email change via the link sent by ``UpdateEmailInProfileView``.

    Redirects to the frontend instead of returning JSON, since this
    endpoint is opened directly in a browser from the email link.
    """
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "change_email_confirm"

    def get(self, request, token):
        """
        Verify the token, change ``email`` and ``username`` and redirect.

        Args:
            request (HttpRequest): The current request.
            token (str): Signed token from ``make_email_change_token``.

        Returns:
            HttpResponseRedirect: 302 to
            ``{FRONTEND_URL}/email-change/success`` on success, or to
            ``{FRONTEND_URL}/email-change/failed`` otherwise.

        Notes:
            - The link works once: the token stores the old email, and
              after the change ``user.email`` no longer matches it. For
              the same reason only the first of several requested links
              can be used.
            - ``username`` is updated together with ``email``, because
              ``create_user`` sets ``username`` to the email and it is
              unique: a stale value would block a new registration with
              the old email.
            - All failure reasons (bad/expired token, unknown user, used
              link, email taken) lead to the same failed page.
            - A failure to send the notification to the old email is
              logged and does not affect the result: the email is
              already changed at that point.
        """
        failed = redirect(f"{settings.FRONTEND_URL}/email-change/failed")

        try:
            payload = read_email_change_token(token)
            user = User.objects.get(pk=payload["user_id"])
        except (signing.BadSignature, KeyError, User.DoesNotExist):
            return failed

        old_email = payload["old_email"]
        new_email = payload["new_email"]

        if user.email != old_email:
            return failed
        if User.objects.filter(email__iexact=new_email).exclude(pk=user.pk).exists():
            return failed

        user.email = new_email
        user.username = new_email
        try:
            with transaction.atomic():
                user.save(update_fields=["email", "username"])
        except IntegrityError:
            return failed

        try:
            send_email_change_notification(user, old_email)
        except Exception:
            logger.exception("Failed to send email change notification to user %s", user.pk)

        return redirect(f"{settings.FRONTEND_URL}/email-change/success")
