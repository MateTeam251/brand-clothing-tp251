from django.urls import path, include
from rest_framework import routers

from products.views import ProductViewSet, CollectionViewSet

router = routers.DefaultRouter()

router.register("collections", CollectionViewSet, basename="collection")
router.register("", ProductViewSet)

urlpatterns = [path("", include(router.urls))]

app_name = "products"
