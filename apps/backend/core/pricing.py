from decimal import Decimal, ROUND_HALF_UP


def calc_discounted(price: Decimal, discount_percent: int) -> str:
    """
    Calculates the discounted price using Decimal arithmetic throughout
    (no float), to avoid rounding-precision errors.

    :param price: Decimal — the original price in the relevant currency.
    :param discount_percent: int — discount size in percent (0-100).
    :return: str — the discounted price, rounded to 2 decimal places
             (ROUND_HALF_UP), returned as a string, e.g. "900.00".
    """
    multiplier = Decimal(100 - discount_percent) / Decimal(100)
    discounted = price * multiplier
    return str(discounted.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def get_discounted_price(obj, currency: str) -> str | None:
    """
    Returns the product's discounted price in the given currency,
    or None if the product has no discount (discount_percent == 0).

    :param obj: Product — the product instance.
    :param currency: str — "usd" or "uah", determines which price field
                     (price_usd/price_uah) is used as the base.
    :return: str | None
    """
    if not obj.discount_percent:
        return None
    price = obj.price_usd if currency == "usd" else obj.price_uah
    return calc_discounted(price, obj.discount_percent)
