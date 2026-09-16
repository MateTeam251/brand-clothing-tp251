import json
import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from payments.providers.wayforpay.callback import handle_callback
from payments.serializers import (
    WayForPayCallbackSerializer,
    WayForPayCallbackResponseSerializer,
)


logger = logging.getLogger("payments.wayforpay")

class WayForPayCallbackView(APIView):
    """
    Server-to-server webhook from WayForPay (serviceUrl).
    The external service doesn't have a JWT token and can send the body without the
    correct Content-Type, so:
    - we don't use DRF authentication,
    - we don't pass this to DRF parsers; we read the request.body ourselves.
    """

    permission_classes = [AllowAny]
    authentication_classes = []
    parser_classes = []

    @extend_schema(
        request=WayForPayCallbackSerializer,
        responses={200: WayForPayCallbackResponseSerializer},
        summary="Handle WayForPay payment callback",
        description=(
                "Receives a server-to-server payment callback from WayForPay,"
                "verifies its signature and processes the payment status."
        ),
    )
    def post(self, request):
        """
        Receives and handles the WayForPay server-to-server callback.
        """
        try:
            if request.body:
                data = json.loads(request.body.decode("utf-8"))
            else:
                data = {}
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            logger.warning("WayForPay callback: invalid JSON body: %s", exc)
            return Response(
                {"detail": "Invalid JSON body"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not isinstance(data, dict):
            logger.warning("WayForPay callback: JSON body is not an object: %r", data)
            return Response(
                {"detail": "Invalid JSON body"},
                status=status.HTTP_400_BAD_REQUEST
            )

        order_reference = data.get("orderReference", "")
        transaction_status = data.get("transactionStatus", "")

        logger.info(
            "WayForPay callback received: orderReference=%s, transactionStatus=%s",
            order_reference,
            transaction_status,
        )

        try:
            response_data = handle_callback(data)
        except ValueError as exc:
            logger.warning(
                "WayForPay callback rejected: orderReference=%s, error: %s",
                order_reference,
                exc,
            )
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception:
            logger.exception(
                "Unexpected error processing WayForPay callback: orderReference=%s",
                order_reference,
            )
            return Response(
                {"detail": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        logger.info(
            "WayForPay callback successfully processed for orderReference=%s",
            order_reference,
        )
        return Response(response_data, status=status.HTTP_200_OK)
