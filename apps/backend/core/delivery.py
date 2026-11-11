from django_countries import countries

from core.enums import DeliveryProvider

BLOCKED_COUNTRIES = {
    "RU",
    "BY",
}


def get_delivery_data_error(provider, delivery_data) -> str | None:
    """
    Returns an error message if delivery_data is invalid for the provider.
    """

    if provider != DeliveryProvider.INTERNATIONAL:
        return None

    country = delivery_data.get("country") if isinstance(delivery_data, dict) else None

    if not isinstance(country, str) or country not in countries:
        return "Select a valid delivery country (ISO code, e.g. UA)."

    if country in BLOCKED_COUNTRIES:
        return "Delivery to this country is not available."

    return None
