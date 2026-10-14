from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import mixins, viewsets

from carts.models import CartItem
from carts.serializers import CartSerializer, CartItemWriteSerializer
from carts.services import get_or_create_active_cart_for
from core.openapi import CURRENCY_PARAM, DETAIL_RESPONSE, VALIDATION_ERROR

WHOSE_CART = ("Works for guests (cart bound to the `sessionid` cookie) and for logged-in users "
              "(Bearer token; the cookie is then not needed).")
ITEM_ID_PARAM = OpenApiParameter("id", OpenApiTypes.INT, OpenApiParameter.PATH,
                                 description="Cart line id (`items[].id` from `GET /api/cart/`).")
ITEM_NOT_FOUND = OpenApiResponse(
    DETAIL_RESPONSE,
    description="No such line in YOUR current cart (lines of other carts are not visible).")


def get_or_create_active_cart(request):
    if request.user.is_authenticated:
        return get_or_create_active_cart_for(user=request.user)

    if not request.session.session_key:
        request.session.create()

    return get_or_create_active_cart_for(session_key=request.session.session_key)


@extend_schema_view(
    retrieve=extend_schema(
        summary="Get my cart",
        description="Returns the current cart; creates an empty one on the first call. " + WHOSE_CART,
        parameters=[CURRENCY_PARAM],
        responses={200: CartSerializer},
    ),
)
@extend_schema(tags=["cart"])
class CartViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """GET /api/cart/ — always returns the caller's own current active cart."""
    serializer_class = CartSerializer

    def get_object(self):
        return get_or_create_active_cart(self.request)



@extend_schema_view(
    create=extend_schema(
        summary="Add to cart",
        description="Adds a product in a size. If this product and size are already in the cart, "
                    "`quantity` is added to that line instead of making a new one. "
                    "Returns the line as stored (with the summed quantity). " + WHOSE_CART,
        responses={201: CartItemWriteSerializer, 400: VALIDATION_ERROR},
    ),
    partial_update=extend_schema(
        summary="Change a cart line",
        description="Send only what changes: `quantity`, `size` or `product`. If the product is out of stock, "
                    "the line can only be reduced (or deleted); raising `quantity`, changing `size` "
                    "or `product` gives 400. " + WHOSE_CART,
        parameters=[ITEM_ID_PARAM],
        responses={200: CartItemWriteSerializer, 400: VALIDATION_ERROR, 404: ITEM_NOT_FOUND},
    ),
    destroy=extend_schema(
        summary="Remove a cart line",
        description=WHOSE_CART,
        parameters=[ITEM_ID_PARAM],
        responses={204: OpenApiResponse(description="Removed. Empty body."), 404: ITEM_NOT_FOUND},
    ),
)
@extend_schema(tags=["cart"])
class CartItemViewSet(mixins.CreateModelMixin,
                       mixins.UpdateModelMixin,
                       mixins.DestroyModelMixin,
                       viewsets.GenericViewSet):
    serializer_class = CartItemWriteSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]


    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["cart"] = get_or_create_active_cart(self.request)
        return context

    def get_queryset(self):
        # CRITICAL: restrict items to the current cart only.
        # Without this filter, a guest or user could DELETE/PATCH someone else's CartItem
        # by ID simply by guessing the number in the URL (IDOR vulnerability).
        cart = get_or_create_active_cart(self.request)
        return CartItem.objects.filter(cart=cart)

    def perform_create(self, serializer):
        serializer.save()
        serializer.instance.cart.save(update_fields=["updated_at"])

    def perform_update(self, serializer):
        serializer.save()
        serializer.instance.cart.save(update_fields=["updated_at"])

    def perform_destroy(self, instance):
        cart = instance.cart
        instance.delete()
        cart.save(update_fields=["updated_at"])
