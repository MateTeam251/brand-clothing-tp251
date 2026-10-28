from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from carts.models import CartStatusEnum
from carts.views import get_or_create_active_cart
from core.openapi import DETAIL_RESPONSE, UNAUTHORIZED, VALIDATION_ERROR, THROTTLED
from orders.models import Order
from orders.serializers import (
    OrderSerializer,
    CheckoutSerializer,
    CheckoutResponseSerializer,
)
from orders.services import checkout, retry_payment

PROVIDER_UNAVAILABLE = OpenApiResponse(
    DETAIL_RESPONSE,
    description="WayForPay is unreachable or returned no payment URL. "
                "The order stays 'pending'; the customer can retry later.",
)


@extend_schema(
    tags=["Orders"],
    summary="Get current customer orders",
    description=(
        "Orders of the authenticated user, newest first. Each order includes its items.\n\n"
        "Orders are identified by `order_reference` (e.g. `ORD-K7M2X9PQ`), the internal "
        "numeric id is never returned. Guest orders are not available here.\n\n"
        "Unpaid orders (`status=pending`) are part of the list."
    ),
    responses={200: OrderSerializer(many=True), 401: UNAUTHORIZED},
)
class CustomerOrderListView(generics.ListAPIView):
    """
    Read-only list of orders belonging to the currently authenticated user.

    The queryset is filtered by ``user=request.user``, so other customers'
    orders are never exposed. Items are prefetched to avoid N+1 queries.
    """

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return only the current user's orders with prefetched items.
        """
        return (
            Order.objects
            .filter(user=self.request.user)
            .prefetch_related("items")
            .order_by("-created_at")
        )


@extend_schema(
    tags=["Orders"],
    summary="Get current customer order",
    description=(
        "One order of the authenticated user, looked up by `order_reference`. "
        "Someone else's order or an unknown reference both give **404**, so the "
        "endpoint can't be used to check which references exist.\n\n"
        "Can be polled by the payment result page while `status` is still `pending`: "
        "the status changes as soon as the WayForPay webhook is processed."
    ),
    responses={
        200: OrderSerializer,
        401: UNAUTHORIZED,
        404: OpenApiResponse(
            DETAIL_RESPONSE, description="Order not found or belongs to another user."
        ),
    },
)
class CustomerOrderDetailView(generics.RetrieveAPIView):
    """
    Single order of the authenticated user.

    Lookup is by ``order_reference``. The queryset is limited to the user's
    own orders, so access control does not depend on the reference being secret.
    """

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "order_reference"

    def get_queryset(self):
        """
        Return only the current user's orders with prefetched items.
        """
        return (
            Order.objects
            .filter(user=self.request.user)
            .prefetch_related("items")
        )


class CheckoutView(APIView):
    """
    Create an order from the current cart and start the WayForPay payment.

    Works for guests and logged-in users. The cart is found the same way as in
    the cart endpoints (guest: ``sessionid`` cookie, user: their active cart).

    Flow:
        1. Validate customer/delivery data (``CheckoutSerializer``).
        2. Take the active cart; it must contain items.
        3. In one DB transaction: build the order from current product prices
           (the client never sends totals), generate ``order_reference``,
           create order items and payment attempt ``<order_reference>-1``.
        4. After commit send the "order created" email.
        5. Ask WayForPay for the payment page URL and return it.

    The cart is NOT cleared here. It is marked converted only when the
    payment is confirmed (webhook or Check Status).
    """

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "checkout"

    @extend_schema(
        tags=["Orders"],
        summary="Checkout the current cart",
        description=(
            "Creates an order (status `pending`) from the current cart and returns the "
            "WayForPay payment page URL. The frontend must redirect the customer to "
            "`payment_url`.\n\n"
            "Prices, discounts and totals are calculated on the server. "
            "The guest cart is identified by the `sessionid` cookie, so the request "
            "must be sent with credentials.\n\n"
            "After payment WayForPay returns the customer to the backend, which redirects to "
            "`{FRONTEND_URL}/payment/result?status=success|failed|pending&order=<order_reference>`."
        ),
        request=CheckoutSerializer,
        responses={
            201: CheckoutResponseSerializer,
            400: OpenApiResponse(
                VALIDATION_ERROR,
                description="Invalid fields, empty/inactive cart, or a product is no longer available.",
            ),
            429: THROTTLED,
            502: PROVIDER_UNAVAILABLE,
        },
    )
    def post(self, request):
        """
        Validate input, create the order and return the payment URL.
        """
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart = self._get_current_cart(request)

        order, payment, payment_url = checkout(
            cart=cart,
            checkout_data=serializer.validated_data,
        )

        response_data = {
            "order_reference": order.order_reference,
            "payment_reference": payment.provider_order_reference,
            "payment_url": payment_url,
        }

        return Response(
            CheckoutResponseSerializer(response_data).data,
            status=status.HTTP_201_CREATED,
        )

    def _get_current_cart(self, request):
        """
        Return the active cart of the guest or authenticated user.

        Raises:
            ValidationError: 400 if the cart is not active or has no items.
        """
        cart = get_or_create_active_cart(request)

        if cart.status != CartStatusEnum.ACTIVE:
            raise ValidationError({"cart": "Cart is not active."})

        if not cart.items.exists():
            raise ValidationError({"cart": "Can not checkout an empty cart."})

        return cart


class RetryPaymentView(APIView):
    """
    Get a payment link for an existing unpaid order.

    Used when the customer closed the payment page or the payment failed.

    Flow:
        1. Find the order by ``order_reference`` among the user's orders (else 404).
        2. Check the last pending attempts with WayForPay (Check Status).
           If one was actually paid, the order becomes ``paid`` and this
           request ends with 400 (nothing to pay).
        3. If a pending attempt younger than 14 minutes has a saved link,
           return that link (WayForPay is not called, a repeated
           ``orderReference`` would be rejected).
        4. Otherwise create attempt ``<order_reference>-N`` and request a new link.
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "retry_payment"

    @extend_schema(
        tags=["Orders"],
        summary="Retry payment for an unpaid order",
        description=(
            "Returns a working payment URL for a `pending` order: either the still "
            "valid link of the latest attempt (younger than 14 minutes) or a new "
            "attempt. Always **201**, also when an existing link is reused.\n\n"
            "Only for authenticated users who own the order. "
            "Guests can't retry yet: they have to checkout again."
        ),
        request=None,
        responses={
            201: CheckoutResponseSerializer,
            400: OpenApiResponse(
                VALIDATION_ERROR,
                description="Order is not `pending` (already paid or canceled).",
            ),
            401: UNAUTHORIZED,
            404: OpenApiResponse(
                DETAIL_RESPONSE,
                description="Order not found or belongs to another user.",
            ),
            429: THROTTLED,
            502: PROVIDER_UNAVAILABLE,
        },
    )
    def post(self, request, order_reference):
        """
        Return a payment URL (reused or newly created) for the user's order.
        """

        order = Order.objects.filter(
            order_reference=order_reference,
            user=request.user,
        ).first()

        if order is None:
            return Response(
                {"detail": "Order not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        order, payment, payment_url = retry_payment(
            order_id=order.id,
        )

        response_data = {
            "order_reference": order.order_reference,
            "payment_reference": payment.provider_order_reference,
            "payment_url": payment_url,
        }

        return Response(
            CheckoutResponseSerializer(response_data).data,
            status=status.HTTP_201_CREATED,
        )
