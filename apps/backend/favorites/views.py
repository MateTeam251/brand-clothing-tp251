from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from favorites.models import Favorite
from favorites.serializers import FavoriteSerializer
from core.openapi import NOT_FOUND, UNAUTHORIZED, VALIDATION_ERROR

FAVORITE_ID_PARAM = OpenApiParameter("id", OpenApiTypes.INT, OpenApiParameter.PATH,
                                     description="Favorite record id (`id`, not `product`).")


@extend_schema_view(
    list=extend_schema(
        summary="My favorites",
        description="Paginated, only the logged-in user's favorites. Archived products are hidden "
                    "(the record is kept and shows up again if the product is unarchived).",
        responses={200: FavoriteSerializer(many=True), 401: UNAUTHORIZED},
    ),
    retrieve=extend_schema(
        summary="One favorite",
        parameters=[FAVORITE_ID_PARAM],
        responses={200: FavoriteSerializer, 401: UNAUTHORIZED, 404: NOT_FOUND},
    ),
    create=extend_schema(
        summary="Add to favorites",
        description="Adding a product that is already in favorites is not an error: "
                    "201 with the existing record, no duplicate is created. An archived product gives 400.",
        responses={201: FavoriteSerializer, 400: VALIDATION_ERROR, 401: UNAUTHORIZED},
    ),
    destroy=extend_schema(
        summary="Remove from favorites by favorite id",
        parameters=[FAVORITE_ID_PARAM],
        responses={204: OpenApiResponse(description="Removed. Empty body."), 401: UNAUTHORIZED, 404: NOT_FOUND},
    ),
    remove_by_product=extend_schema(
        summary="Remove from favorites by product id",
        description="For the heart button on a product card, which knows only the product id.",
        parameters=[OpenApiParameter("product_id", OpenApiTypes.INT, OpenApiParameter.PATH,
                                     description="Product id.")],
        responses={
            204: OpenApiResponse(description="Removed. Empty body."),
            401: UNAUTHORIZED,
            404: OpenApiResponse(description="This product is not in favorites. Empty body."),
        },
    ),
)
@extend_schema(tags=["favorites"])
class FavoriteViewSet(viewsets.ModelViewSet):
    """
    Manage the authenticated user's favorite products.

    GET (list) returns only the current user's favorites, without archived products.
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
        return Favorite.objects.filter(user=self.request.user, product__is_archived=False)


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

