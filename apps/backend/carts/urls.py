from django.urls import path
from rest_framework.routers import DefaultRouter
from carts.views import CartViewSet, CartItemViewSet

app_name = "carts"

router = DefaultRouter()
router.register(r"items", CartItemViewSet, basename="cart-item")

urlpatterns = [
    path("", CartViewSet.as_view({"get": "list"}), name="cart-detail"),
] + router.urls
