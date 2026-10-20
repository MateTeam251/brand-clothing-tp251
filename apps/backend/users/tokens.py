from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import base36_to_int
from django.conf import settings


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    """
    Simple helper function to generate an Activation Token for a user
    """
    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{timestamp}{user.is_active}"

    def check_token(self, user, token):
        if not super().check_token(user, token):
            return False
        ts = base36_to_int(token.split("-")[0])
        return self._num_seconds(self._now()) - ts <= settings.ACTIVATION_TOKEN_TIMEOUT




account_activation_token = AccountActivationTokenGenerator()
