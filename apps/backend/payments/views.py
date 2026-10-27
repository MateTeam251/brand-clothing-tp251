import json
import logging
from urllib.parse import urlencode

from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiResponse
from rest_framework import status, serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from core.enums import PaymentStatus, PaymentProvider, OrderStatus
from core.openapi import DETAIL_RESPONSE
from payments.models import Payment
from payments.providers.wayforpay.callback import handle_callback, sync_payment_status
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
        tags=["Payments"],
        summary="WayForPay payment webhook (serviceUrl)",
        description=(
            "Server-to-server callback from WayForPay. Not called by the frontend.\n\n"
            "1. Required fields and `merchantAccount` are checked.\n"
            "2. `merchantSignature` (HMAC-MD5) is verified. Invalid signature gives **400** "
            "and nothing changes.\n"
            "3. The attempt is found by `provider_order_reference` (`ORD-XXXXXXXX-<attempt>`); "
            "amount and currency must match the attempt.\n"
            "4. Result is applied idempotently:\n\n"
            "| transactionStatus | effect |\n"
            "|---|---|\n"
            "| `Approved` | attempt `successful`, order `paid`, cart converted, 'paid' email after commit |\n"
            "| `Approved` for an order that is already paid | attempt `duplicate` + "
            "`needs_refund` in `payment_data` (manual refund), error is logged |\n"
            "| `Declined`, `Expired` | attempt `failed` (only if it was `pending`) |\n"
            "| anything else | logged, nothing changes |\n\n"
            "The response is the signed `accept` WayForPay expects "
            "(`orderReference`, `status`, `time`, `signature`). "
            "Any non-accept response makes WayForPay repeat the webhook, "
            "which is safe because processing is idempotent."
        ),
        request=WayForPayCallbackSerializer,
        responses={
            200: WayForPayCallbackResponseSerializer,
            400: OpenApiResponse(
                DETAIL_RESPONSE,
                description="Invalid JSON, missing fields, bad signature, unknown payment or amount mismatch.",
            ),
            500: OpenApiResponse(DETAIL_RESPONSE, description="Unexpected error."),
        },
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
        except (ValueError, ValidationError) as exc:
            logger.warning(
                "WayForPay callback rejected: orderReference=%s, error: %s",
                order_reference,
                exc,
            )
            detail_msg = (
                exc.messages[0] if isinstance(exc, ValidationError) else str(exc)
            )
            return Response(
                {"detail": detail_msg},
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


@extend_schema(
    tags=["Payments"],
    summary="WayForPay browser return (returnUrl)",
    description=(
        "Opened by the customer's **browser** after paying on the WayForPay page "
        "(POST with form data, sometimes GET). Not called by the frontend.\n\n"
        "Only `orderReference` from the request is used, and only to find the payment "
        "attempt. It is **not** proof of payment. If the attempt is still `pending` "
        "(webhook not processed yet), the backend asks WayForPay for the real status "
        "(Check Status) and applies it. Then it redirects (**303**) to "
        "`{FRONTEND_URL}/payment/result?status=<status>&order=<order_reference>`.\n\n"
        "| status | meaning |\n"
        "|---|---|\n"
        "| `success` | order is `paid` |\n"
        "| `failed` | attempt declined/expired, or unknown/missing reference "
        "(no `order` param in the last two cases) |\n"
        "| `pending` | bank is still processing; a confirmation email will follow |\n\n"
        "The frontend must not treat `status` in the URL as confirmation: anyone can type it. "
        "The real state is `GET /api/orders/<order_reference>/`."
    ),
    request=inline_serializer(
        "WayForPayReturnForm", {"orderReference": serializers.CharField()}
    ),
    responses={
        303: OpenApiResponse(description="Redirect to the frontend payment result page."),
        429: OpenApiResponse(description="Too many requests (30/min)."),
    },
)
class PaymentReturnView(APIView):
    """
    Browser return from WayForPay (returnUrl).

    The request data only identifies the payment attempt and is never trusted
    as payment confirmation. The status is read from our DB, refreshed through
    WayForPay Check Status when the attempt is still pending.
    Races with the serviceUrl webhook are safe: both go through
    ``_apply_payment_result``, which locks the rows and is idempotent.
    """

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "payment_return"

    def get(self, request, *args, **kwargs):
        return self._handle(request)

    def post(self, request, *args, **kwargs):
        return self._handle(request)

    def _handle(self, request):
        reference = (
            request.data.get("orderReference")
            or request.query_params.get("orderReference")
        )

        if not reference:
            logger.warning("WayForPay return without orderReference")
            return self._redirect("failed")

        payment = (
            Payment.objects
            .filter(
                provider=PaymentProvider.WAYFORPAY,
                provider_order_reference=reference,
            )
            .first()
        )

        if payment is None:
            logger.warning("WayForPay return for unknown reference: %s", reference)
            return self._redirect("failed")

        if payment.status == PaymentStatus.PENDING:
            try:
                payment = sync_payment_status(payment)
            except Exception:
                logger.exception("Return sync failed for %s", reference)

        order = payment.order

        return self._redirect(self._resolve_status(order, payment), order.order_reference)

    @staticmethod
    def _resolve_status(order, payment) -> str:
        if order.status == OrderStatus.PAID:
            return "success"
        if payment.status == PaymentStatus.FAILED:
            return "failed"
        return "pending"

    @staticmethod
    def _redirect(result: str, order_reference: str | None = None):
        params = {"status": result}
        if order_reference:
            params["order"] = order_reference

        return HttpResponseRedirect(
            f"{settings.FRONTEND_URL}/payment/result?{urlencode(params)}",
            status=status.HTTP_303_SEE_OTHER,
        )
