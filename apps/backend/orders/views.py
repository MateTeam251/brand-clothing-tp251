from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView

from orders.models import Order
from orders.serializers import OrderSerializer, CheckoutSerializer
from orders.services import create_order_from_cart


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
        request=CheckoutSerializer,
    )
    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        #TODO: Cart is not implemented yet

        cart = self._get_current_cart(request)

        order, payment = create_order_from_cart(
            cart=cart,
            checkout_data=serializer.validated_data,
        )

    def _get_current_cart(self, request):
        raise NotImplementedError("Cart is not implemented yet")
