from django.contrib.auth.models import (AbstractUser,
                                        UserManager)
from django.db import models


class CustomUserManager(UserManager):
    """
    Custom manager for the ``User`` model.

    Replaces Django's default username-based user creation with an
    email-based flow, since ``User.USERNAME_FIELD`` is set to "email".
    """
    def create_user(self, email=None, password=None, **extra_fields):
        """
        Create and save a regular user with the given email and password.

        Args:
            email (str): The user's email address. Required.
            password (str): The raw password to hash and store.
            **extra_fields: Any additional fields defined on the User
                model (e.g. first_name, phone_number, birth_date).

        Raises:
            ValueError: If ``email`` is not provided.

        Returns:
            User: The newly created user instance.

        Notes:
            - The email is normalized via ``normalize_email`` (lowercases
              the domain part).
            - ``username`` is autofilled with the email if not explicitly
              passed in ``extra_fields``, since ``AbstractUser`` still
              defines a ``username`` field with a unique constraint.
            - The password is hashed via ``set_password``; it is never
              stored in plain text.
        """
        if not email:
            raise ValueError("User must have an email address")
        email = self.normalize_email(email)
        extra_fields.setdefault("username", email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email=None, password=None, **extra_fields):
        """
        Create and save a superuser with the given email and password.

        Args:
            email (str): The user's email address. Required.
            password (str): The raw password to hash and store.
            **extra_fields: Any additional fields defined on the User
                model. ``is_staff``, ``is_superuser`` and ``is_active``
                are forced to True unless already provided.

        Raises:
            ValueError: If ``email`` is not provided.

        Returns:
            User: The newly created superuser instance.

        Notes:
            Unlike regular users created via ``create_user`` (where
            ``is_active`` defaults to False on the model), superusers
            are explicitly activated here so they can log in immediately,
            e.g. via ``manage.py createsuperuser``.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if not email:
            raise ValueError("Superuser must have an email address")

        return self.create_user(email=email, password=password, **extra_fields)


class User(AbstractUser):
    """
    Custom user model that authenticates via email instead of username.

    Extends Django's ``AbstractUser`` to add project-specific fields and
    swaps the login identifier from ``username`` to ``email`` (see
    ``USERNAME_FIELD`` below). The inherited ``username`` field is kept
    for compatibility but is not used for authentication; it is
    autopopulated with the user's email by ``CustomUserManager``.

    Attributes:
        email (EmailField): Unique email address. Used as the login
            identifier instead of username.
        first_name, last_name (CharField): Inherited from
            ``AbstractUser`` (max length 150, ``blank=True``). Required
            on registration and cannot be emptied in the profile; this
            is enforced by the serializers, not the model.
        birth_date (DateField): User's date of birth. Optional
            (nullable and blank).
        marketing_opt_in (BooleanField): Whether the user has opted in
            to receive marketing communications. Defaults to False.
        instagram (TextField): User's Instagram handle or profile link.
            Optional (``blank=True``).
        telegram (CharField): User's Telegram handle, max length 120.
            Optional (``blank=True``), defaults to an empty string.
        phone_number (CharField): User's phone number, max length 20.
            ``blank=True`` at the model level (existing users may have
            none), but required by the registration and profile
            serializers. Not nullable; empty value is an empty string.
        is_active (BooleanField): Overrides the default from
            ``AbstractUser``. Defaults to False, meaning newly created
            users are inactive until explicitly activated (e.g. via an
            email confirmation / activation flow).

    Class attributes:
        USERNAME_FIELD (str): Set to "email" — Django will use this
            field for authentication (login) instead of "username".
        REQUIRED_FIELDS (list): Empty — no extra fields (besides email
            and password) are prompted for when running
            ``manage.py createsuperuser``.
        objects (CustomUserManager): Custom manager handling email-based
            user/superuser creation.
    """
    email = models.EmailField(unique=True)
    birth_date = models.DateField(blank=True, null=True)

    marketing_opt_in = models.BooleanField(default=False)
    instagram = models.TextField(blank=True)
    telegram = models.CharField(max_length=120, blank=True, default="")

    phone_number = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=False)


    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()
