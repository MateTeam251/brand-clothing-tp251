from rest_framework import status
from rest_framework.exceptions import APIException


class PaymentProviderUnavailable(APIException):
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = "Payment service is temporarily unavailable. Please try again later."
    default_code = "payment_provider_unavailable"
