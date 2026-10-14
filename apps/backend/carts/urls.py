from django.urls import path
from rest_framework.routers import DefaultRouter
from carts.views import CartViewSet, CartItemViewSet

app_name = "carts"

router = DefaultRouter()
router.register(r"items", CartItemViewSet, basename="cart-item")

urlpatterns = [
    # retrieve, not list: the cart is one object, so the schema shows no pagination
    path("", CartViewSet.as_view({"get": "retrieve"}), name="cart-detail"),
] + router.urls
