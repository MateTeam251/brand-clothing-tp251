import phonenumbers
from rest_framework import serializers


def normalize_phone(value: str) -> str:
    """
    Parses the phone, checks that it is a real number and returns it in
    E.164 format (+380501234567).
    """
    value = value.strip()
    try:
        parsed = phonenumbers.parse(value, None)
    except phonenumbers.NumberParseException:
        raise serializers.ValidationError(
            "Enter a valid phone number in international format."
        )

    if not phonenumbers.is_valid_number(parsed):
        raise serializers.ValidationError("Enter a valid phone number.")

    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
