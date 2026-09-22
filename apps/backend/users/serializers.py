from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils.encoding import force_str
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from users.utils import send_password_reset_link
from carts.services import merge_guest_cart_into_user_cart



User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer used to register a new user.

    Accepts the core signup fields and delegates user creation to
    ``User.objects.create_user`` (via ``CustomUserManager``), which
    handles password hashing and email normalization.

    Notes:
        - The created user will have ``is_active=False`` by default
          (per the model definition), so an activation step (e.g. email
          confirmation) is expected to happen afterwards.
        - ``password`` is write-only and never included in the
          serialized output.
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    agree_to_terms = serializers.BooleanField(write_only=True)
    marketing_opt_in = serializers.BooleanField(required=False, default=False)


    class Meta:
        model = User
        fields = ("email", "password", "password_confirm", "name", "instagram",
                  "agree_to_terms", "marketing_opt_in")


    def validate_agree_to_terms(self, value):
        if not value:
            raise serializers.ValidationError("You must agree to the terms and privacy policy.")
        return value


    def validate(self, attrs):
        """
        Object-level validation: runs after all individual fields pass
        their own validation. Used here because comparing two fields
        against each other can't be expressed as a single-field validator.
        """

        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match"})
        return attrs

    def create(self, validated_data):
        """
        Create a new user from validated data.

        Args:
            validated_data (dict): Validated fields, including the
                plain-text ``password`` and optional ``address``.

        Returns:
            User: The newly created (inactive) user instance.
        """
        validated_data.pop("password_confirm") # not a model field - must be removed
        validated_data.pop("agree_to_terms") # not a model field - must be removed
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Token obtain serializer that blocks login for inactive accounts.

    Extends SimpleJWT's default serializer to add an activation check:
    even if the email/password pair is valid, a JWT pair will not be
    issued unless ``user.is_active`` is True.
    """
    def validate(self, attrs):
        """
        Validate credentials and enforce that the account is active.

        Args:
            attrs (dict): Input data (typically email and password).

        Raises:
            serializers.ValidationError: If the account exists and the
                credentials are correct, but the account is not yet
                activated.

        Returns:
            dict: Token pair data (access/refresh), as produced by the
            parent ``TokenObtainPairSerializer``.
        """
        data = super().validate(attrs)
        if not self.user.is_active:
            raise serializers.ValidationError("Account is not activated. Check your email.")
        request = self.context.get("request")
        if request is not None:
            try:
                merge_guest_cart_into_user_cart(request, self.user)
            except Exception:
                pass

        return data


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for reading and updating the authenticated user's profile.

    ``id`` and ``email`` are read-only: the user's email cannot be
    changed through this serializer (e.g. to avoid breaking the
    email-based login identifier without a dedicated change-email flow).

    ``addresses`` is read-only here — managing (adding/editing/deleting)
    addresses is handled through a dedicated AddressViewSet, not through
    this profile endpoint.
    """

    class Meta:
        model = User
        fields = ["id", "email", "name", "age", "phone_number",
                  "marketing_opt_in", "instagram",]
        read_only_fields = ['id', 'email']

    def update(self, instance, validated_data):

        # update simple User fields as usual
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer that handles the "forgot password" request step.

    Given an email address, triggers a password reset email if a
    matching account exists.
    """
    email = serializers.EmailField()

    def save(self, **kwargs):
        """
        Send a password reset link to the given email, if the user exists.

        Args:
            **kwargs: Expects ``request`` (the current HTTP request),
                passed through to ``send_password_reset_link`` so it can
                build an absolute reset URL.

        Returns:
            None

        Security note:
            Deliberately does not raise or reveal whether the email
            exists in the system (silently returns on
            ``User.DoesNotExist``), to avoid leaking which emails are
            registered (user enumeration).
        """
        request = kwargs.get("request")
        email = self.validated_data["email"]

        try:
            user = User.objects.get(email=email)

        except User.DoesNotExist:
            return

        send_password_reset_link(request, user)




class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer that handles the "reset password" confirmation step.

    Validates the uid/token pair from the reset link (as generated by
    ``send_password_reset_link`` / Django's ``default_token_generator``)
    and sets the new password if everything checks out.
    """
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value):
        """
        Run the new password through Django's password validators.

        Args:
            value (str): The proposed new plain-text password.

        Raises:
            serializers.ValidationError: If the password fails any of
                Django's configured ``AUTH_PASSWORD_VALIDATORS``
                (e.g. too common, too similar to user attributes, etc.).

        Returns:
            str: The validated password, unchanged.
        """
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.message))
        return value



    def validate(self, attrs):
        """
        Decode the uid and verify the reset token.

        Args:
            attrs (dict): Contains ``uid``, ``token`` and
                ``new_password``.

        Raises:
            serializers.ValidationError: Under the key "uid" if the uid
                cannot be decoded or does not match an existing user;
                under the key "token" if the token is invalid or expired.

        Returns:
            dict: The original attrs, with the resolved ``user``
            instance added under the "user" key for use in ``save``.
        """
        try:
            uid = force_str(urlsafe_base64_decode(attrs['uid']))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            raise serializers.ValidationError({"uid": "Invalid or expired link."})

        if not default_token_generator.check_token(user, attrs['token']):
            raise serializers.ValidationError({"token": "Invalid or expired token."})

        attrs['user'] = user
        return attrs

    def save(self):
        """
        Set the new password on the resolved user and persist it.

        Requires ``validate`` to have already run (so ``self.validated_data
        ['user']`` is populated).

        Returns:
            User: The user instance with the updated (hashed) password.
        """
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
