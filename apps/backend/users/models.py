from django.contrib.auth.models import (AbstractUser,
                                        UserManager)
from django.db import models
from django_countries.fields import CountryField

from core.enums import DeliveryProvider

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
                model (e.g. name, phone_number, age).

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
        age (PositiveSmallIntegerField): User's age. Optional
            (nullable and blank).
        marketing_opt_in (BooleanField): Whether the user has opted in
            to receive marketing communications. Defaults to False.
        instagram (TextField): User's Instagram handle or profile link.
            NOTE: this field has no ``blank=True``/``null=True``, so it
            is effectively required by forms/serializers unless a
            default is supplied — double-check this is intentional.
        phone_number (CharField): User's phone number, max length 20.
            Optional in forms (``blank=True``) but defaults to an
            empty string at the database level (not nullable).
        is_active (BooleanField): Overrides the default from
            ``AbstractUser``. Defaults to False, meaning newly created
            users are inactive until explicitly activated (e.g. via an
            email confirmation / activation flow).
        name (TextField): Free-text display name. Optional (blank=True).

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
    age = models.PositiveSmallIntegerField(null=True, blank=True)

    marketing_opt_in = models.BooleanField(default=False)
    instagram = models.TextField()

    phone_number = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=False)

    name = models.TextField(blank=True)


    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()


class Address(models.Model):
    """
    A shipping address belonging to a user.

    Fields are split (rather than one free-text field) to support
    international shipping — validation, filtering, and integration
    with delivery provider APIs (Nova Poshta, UkrPoshta, DHL) all need
    structured data, not a single blob of text.

    Not every field applies to every country (e.g. "region/state" is
    meaningless in some countries) — most are left optional, and the
    frontend should adapt the form based on the selected country.
    """

    user = models.OneToOneField(
        "users.User", on_delete=models.CASCADE, related_name="address"
    )

    country = CountryField() # ISO 3166-1 alpha-2, e.g. "UA", "US", "DE"

    full_name = models.CharField(max_length=255)  # recipient's name — may differ from account owner
    phone_number = models.CharField(max_length=20)

    region = models.CharField(max_length=100, blank=True)  # region / state / province
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True)  # not all countries use one

    address_line_1 = models.CharField(max_length=255)  # street + house number
    address_line_2 = models.CharField(max_length=255, blank=True)  # apartment, floor, etc.

    # Optional: for carrier-specific delivery points (e.g. Nova Poshta branch number)
    delivery_provider = models.CharField(
        max_length=30,
        choices=DeliveryProvider.choices, # type: ignore[arg-type]
        blank=True
    )
    delivery_point = models.CharField(max_length=255, blank=True)  # e.g. "Branch #25" Should probably be able to choose from Nova Poshta or ukr poshta integrated list of branches


    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} — {self.city}, {self.country}"

