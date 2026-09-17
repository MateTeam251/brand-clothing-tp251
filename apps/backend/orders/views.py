from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from orders.models import Order
from orders.serializers import OrderSerializer


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
    Return orders belonging to the currently authenticated user.
    """

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
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
    Return a single order belonging to the currently authenticated user.
    """

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Order.objects
            .filter(user=self.request.user)
            .prefetch_related(
                "items",
            )
        )
