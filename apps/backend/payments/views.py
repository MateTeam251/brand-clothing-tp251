from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.parsers import JSONParser, FormParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from payments.providers.wayforpay.callback import handle_callback
from payments.serializers import (
    WayForPayCallbackSerializer,
    WayForPayCallbackResponseSerializer,
)


class WayForPayCallbackView(APIView):
    permission_classes = [AllowAny]

    parser_classes = [JSONParser, FormParser]

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
            response_data = handle_callback(request.data)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(response_data)
