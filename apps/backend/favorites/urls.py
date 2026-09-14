from django.urls import path, include
from rest_framework import routers

from favorites.views import FavoriteViewSet

router = routers.DefaultRouter()

router.register("", FavoriteViewSet)

urlpatterns = [path("", include(router.urls))]

app_name = "favorites"
