from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import Order
from orders.serializers import (
    OrderSerializer,
    CheckoutSerializer,
    CheckoutResponseSerializer,
)
from orders.services import checkout, retry_payment


@extend_schema(
    tags=["Orders"],
    summary="Get current customer orders",
    description=(
        "Returns orders belonging to the currently authenticated user."
        "Guest orders are not available through this endpoint."
    ),
    responses=OrderSerializer(many=True),
)
class CustomerOrderListView(generics.ListAPIView):
    """
    Read-only list of orders belonging to the currently authenticated user.

    Only authenticated customers have access to this address.
    Orders belonging to other users are excluded from the queryset.
    """

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Returns only orders belonging to the currently authenticated user.

        Pre-fetches order items to avoid additional database queries
        when serializing the order list.
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
        "Returns one order belonging to the currently authenticated user."
    ),
    responses=OrderSerializer,
)
class CustomerOrderDetailView(generics.RetrieveAPIView):
    """
    A detailed read-only view of a single order belonging to the current customer.

    The queryset is restricted to the authorized user's orders,
    so a customer cannot retrieve another customer's order by ID.
    """

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Returns only orders belonging to the currently authenticated user.

        Pre-fetches order items, as they are included in the response.
        """
        return (
            Order.objects
            .filter(user=self.request.user)
            .prefetch_related(
                "items",
            )
        )


class CheckoutView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Orders"],
        summary="Checkout current cart",
        description=(
            "Creates an order from cart data and returns the payment gateway redirect URL."
        ),
        request=CheckoutSerializer,
        responses={201: CheckoutResponseSerializer},
    )
    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # TODO: Cart is not implemented yet

        cart = self._get_current_cart(request)

        order, payment, payment_url = checkout(
            cart=cart,
            checkout_data=serializer.validated_data,
        )

        response_data = {
            "order_id": order.id,
            "payment_id": payment.id,
            "payment_url": payment_url,
        }

        return Response(
            CheckoutResponseSerializer(response_data).data,
            status=status.HTTP_201_CREATED,
        )

    def _get_current_cart(self, request):
        raise NotImplementedError("Cart is not implemented yet")


class RetryPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Orders"],
        summary="Retry payment for an unpaid order",
        description=(
            "Creates a new payment attempt for an existing pending order."
        ),
        responses={
            201: CheckoutResponseSerializer,
            404: OpenApiResponse(description="Order not found or access denied"),
        },
    )
    def post(self, request, order_id):
        """
        Create a new payment attempt for the customer's pending order.
        """

        order = Order.objects.filter(
            pk=order_id,
            user=request.user,
        ).first()

        if order is None:
            return Response(
                {"detail": "Order not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        order, payment, payment_url = retry_payment(
            order_id=order_id,
        )

        response_data = {
            "order_id": order.id,
            "payment_id": payment.id,
            "payment_url": payment_url,
        }

        return Response(
            CheckoutResponseSerializer(response_data).data,
            status=status.HTTP_201_CREATED,
        )
