from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from favorites.models import Favorite
from favorites.serializers import FavoriteSerializer


class FavoriteViewSet(viewsets.ModelViewSet):
    """
    Manage the authenticated user's favorite products.

    GET (list) returns only the current user's favorites.
    POST adds a product to favorites (product id in the body).
    DELETE removes a favorite.
    PUT/PATCH are disabled — a favorite is either present or not,
    there's nothing to "update" on it.
    """
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "delete", "head", "options"]


    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)


    def perform_create(self, serializer):
        favorite, _ = Favorite.objects.get_or_create(
            user=self.request.user,
            product=serializer.validated_data["product"]
        )
        serializer.instance = favorite


    @action(detail=False, methods=["delete"], url_path="by-product/(?P<product_id>[^/.]+)")
    def remove_by_product(self, request, product_id=None):
        """
        Remove a favorite by product id, without the frontend needing
        to know the Favorite record's own id — useful for a toggle
        button on a product card that only knows the product's id.
        """
        deleted, _ = Favorite.objects.filter(user=request.user, product_id=product_id).delete()
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_404_NOT_FOUND)

