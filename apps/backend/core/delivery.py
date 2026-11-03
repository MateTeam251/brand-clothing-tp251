from core.enums import DeliveryProvider

NOVA_POST_COUNTRIES = {
    "PL": {"ua": "Польща", "en": "Poland"},
    "DE": {"ua": "Німеччина", "en": "Germany"},
    "CZ": {"ua": "Чехія", "en": "Czech Republic"},
    "RO": {"ua": "Румунія", "en": "Romania"},
    "MD": {"ua": "Молдова", "en": "Moldova"},
    "LT": {"ua": "Литва", "en": "Lithuania"},
    "LV": {"ua": "Латвія", "en": "Latvia"},
    "EE": {"ua": "Естонія", "en": "Estonia"},
    "IT": {"ua": "Італія", "en": "Italy"},
    "ES": {"ua": "Іспанія", "en": "Spain"},
    "FR": {"ua": "Франція", "en": "France"},
    "HU": {"ua": "Угорщина", "en": "Hungary"},
    "SK": {"ua": "Словаччина", "en": "Slovakia"},
    "AT": {"ua": "Австрія", "en": "Austria"},
    "NL": {"ua": "Нідерланди", "en": "Netherlands"},
    "GB": {"ua": "Велика Британія", "en": "United Kingdom"},
}


def get_delivery_data_error(provider, delivery_data) -> str | None:
    """
    Returns an error message if delivery_data is invalid for the provider.
    """

    if provider != DeliveryProvider.NOVA_POST:
        return None

    country = delivery_data.get("country") if isinstance(delivery_data, dict) else None

    if not isinstance(country, str) or country not in NOVA_POST_COUNTRIES:
        return "Select a supported delivery country."

    return None
