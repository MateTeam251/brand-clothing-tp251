from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import base36_to_int
from django.conf import settings
from django.utils.crypto import constant_time_compare


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
