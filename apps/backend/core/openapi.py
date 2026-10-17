"""
Shared pieces of the OpenAPI (Swagger) schema, so query parameters and error
responses are described the same way on every endpoint.
"""
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, inline_serializer
from rest_framework import serializers

LANG_PARAM = OpenApiParameter(
    "lang",
    OpenApiTypes.STR,
    enum=["ua", "en"],
    default="ua",
    description="Language of translatable fields (description, type, fabric composition). "
                "Only `en` switches to English; any other value or no value gives Ukrainian.",
)

CURRENCY_PARAM = OpenApiParameter(
    "currency",
    OpenApiTypes.STR,
    enum=["uah", "usd"],
    default="uah",
    description="Currency of every price in the response. "
                "Only `usd` switches to dollars; any other value or no value gives hryvnia.",
)

DETAIL_RESPONSE = inline_serializer(
    "DetailMessage",
    {"detail": serializers.CharField(help_text="Human-readable message.")},
)

VALIDATION_ERROR = OpenApiResponse(
    description="Validation error. The body maps each invalid field to a list of messages, "
                'e.g. `{"email": ["This field is required."]}`. Errors that are not tied to '
                "one field come under `non_field_errors`.",
)
UNAUTHORIZED = OpenApiResponse(
    DETAIL_RESPONSE,
    description="No `Authorization: Bearer <access>` header, or the access token is invalid/expired.",
)
NOT_FOUND = OpenApiResponse(DETAIL_RESPONSE, description="Object not found.")
