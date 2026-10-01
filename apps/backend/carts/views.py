from rest_framework import mixins, viewsets
from rest_framework.response import Response

from carts.models import Cart, CartItem, CartStatusEnum
from carts.serializers import CartSerializer, CartItemWriteSerializer


def get_or_create_active_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user, status=CartStatusEnum.ACTIVE)
        return cart

    if not request.session.session_key:
        request.session.create()

    cart, _ = Cart.objects.get_or_create(
        session_key=request.session.session_key,
        user__isnull=True,
        status=CartStatusEnum.ACTIVE,
    )
    return cart


class CartViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """GET /api/cart/ — always returns the caller's own current active cart."""
    serializer_class = CartSerializer

    def get_object(self):
        return get_or_create_active_cart(self.request)

    def list(self, request, *args, **kwargs):
        cart = self.get_object()
        return Response(self.get_serializer(cart).data)



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
