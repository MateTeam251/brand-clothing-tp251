from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import signing
from django.utils.http import base36_to_int
from django.conf import settings
from django.utils.crypto import constant_time_compare

EMAIL_CHANGE_SALT = "users.email_change"


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    """
    Simple helper function to generate an Activation Token for a user
    """
    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{timestamp}{user.is_active}"

    def check_token(self, user, token):
        """
        Same as Django's check, but the lifetime comes from
        ``ACTIVATION_TOKEN_TIMEOUT`` instead of ``PASSWORD_RESET_TIMEOUT``.
        """
        if not (user and token):
            return False
        try:
            ts_b36, _ = token.split("-")
            ts = base36_to_int(ts_b36)
        except ValueError:
            return False

        for secret in [self.secret, *self.secret_fallbacks]:
            if constant_time_compare(self._make_token_with_timestamp(user, ts, secret), token):
                break
        else:
            return False

        return self._num_seconds(self._now()) - ts <= settings.ACTIVATION_TOKEN_TIMEOUT


account_activation_token = AccountActivationTokenGenerator()


def make_email_change_token(user, new_email):
    """
    Build a signed token for confirming an email change.

    The token carries the user's pk, the current (old) email and the
    requested new email, so nothing has to be stored in the database.

    Args:
        user (User): The user requesting the change.
        new_email (str): The validated new email address.

    Returns:
        str: URL-safe signed token.

    Notes:
        The token is signed, not encrypted: its payload can be decoded
        by anyone who has it, but it cannot be forged or modified.
    """
    payload = {
        "user_id": user.pk,
        "old_email": user.email,
        "new_email": new_email,
    }
    return signing.dumps(payload, salt=EMAIL_CHANGE_SALT)


def read_email_change_token(token):
    """
    Verify an email change token and return its payload.

    Args:
        token (str): Token produced by ``make_email_change_token``.

    Raises:
        signing.BadSignature: If the token is malformed or tampered with.
        signing.SignatureExpired: If the token is older than
            ``settings.EMAIL_CHANGE_TOKEN_TIMEOUT`` (subclass of
            ``BadSignature``, so catching ``BadSignature`` covers both).

    Returns:
        dict: Payload with ``user_id``, ``old_email`` and ``new_email``.
    """
    return signing.loads(
        token,
        salt=EMAIL_CHANGE_SALT,
        max_age=settings.EMAIL_CHANGE_TOKEN_TIMEOUT,
    )
