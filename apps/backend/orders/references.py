import secrets

from django.conf import settings
from hashids import Hashids

_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

_hashids = Hashids(
    salt=settings.SECRET_KEY,
    min_length=4,
    alphabet=_ALPHABET,
)


def build_order_reference(order_id: int) -> str:
    """
    Creates a public order number: ORD-<masked id><6 random characters>.

    The id part ensures uniqueness, the random suffix makes the number
    unguessable. The number is only stored and searched, never decoded.
    """

    suffix = "".join(secrets.choice(_ALPHABET) for _ in range(6))
    return f"ORD-{_hashids.encode(order_id)}{suffix}"
