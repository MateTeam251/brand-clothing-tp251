from rest_framework import generics, status
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from core.openapi import DETAIL_RESPONSE, UNAUTHORIZED, VALIDATION_ERROR
from users.serializers import (RegisterSerializer,
                               UserProfileSerializer,
                               PasswordResetConfirmSerializer,
                               PasswordResetRequestSerializer,
                               CustomTokenObtainPairSerializer,
                               LogoutSerializer)
from users.tokens import account_activation_token
from users.utils import send_activation_email

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

    @extend_schema(
        tags=["auth"],
        summary="Activate an account (link from the email)",
        description="Opened from the activation email, not called by the frontend. `uidb64` and "
                    "`token` are the two last parts of the link. Returns an **HTML page**, not JSON. "
                    "Opening a valid link again is fine: the success page is shown again.",
        responses={
            (200, "text/html"): OpenApiResponse(OpenApiTypes.STR, description="Account activated."),
            (400, "text/html"): OpenApiResponse(OpenApiTypes.STR, description="Invalid or expired link."),
        },
    )
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


@extend_schema_view(
    get=extend_schema(summary="Get my profile", responses={200: UserProfileSerializer, 401: UNAUTHORIZED}),
    put=extend_schema(
        summary="Replace my profile",
        description="Full update: `instagram` must be sent, other fields not sent are left as they are. "
                    "`id` and `email` cannot be changed.",
        responses={200: UserProfileSerializer, 400: VALIDATION_ERROR, 401: UNAUTHORIZED},
    ),
    patch=extend_schema(
        summary="Update my profile",
        description="Partial update: send only the fields to change. `id` and `email` cannot be changed.",
        responses={200: UserProfileSerializer, 400: VALIDATION_ERROR, 401: UNAUTHORIZED},
    ),
)
@extend_schema(tags=["profile"])
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
    description="Sends a reset link if an account with this email exists. The response is the same "
                "whether it exists or not, so it can't be used to check which emails are registered.",
    request=PasswordResetRequestSerializer,
    responses={
        200: OpenApiResponse(DETAIL_RESPONSE, description="Always, for any valid email."),
        400: VALIDATION_ERROR,
    },
)
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


@extend_schema(
    tags=["auth"],
    summary="Set a new password (link from the email)",
    description="`uidb64` and `token` are the two last parts of the reset link from the email. "
                "A link works once: after the password is changed it becomes invalid.",
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
