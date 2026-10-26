from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics

from delivery.factory import SYNCED_PROVIDERS
from delivery.models import DeliveryCity, DeliveryBranch
from delivery.serializers import DeliveryCitySerializer, DeliveryBranchSerializer
from django.db.models import Case, IntegerField, Value, When
from delivery.pagination import DeliveryCityPagination, DeliveryBranchPagination


@extend_schema(
    tags=["delivery"],
    summary="Search delivery cities",
    description="Paginated, always 30 per page (`limit` is ignored). With `search`, the exact name match "
                "comes first, then names starting with it, then the rest; each group in alphabetical "
                "order. Village names include the region, e.g. `Антонівка (Київська обл.)`.",
    parameters=[
        OpenApiParameter("provider", OpenApiTypes.STR, enum=SYNCED_PROVIDERS,
                         description="Delivery provider. Omit to search all providers."),
        OpenApiParameter("country", OpenApiTypes.STR,
                         description="ISO 3166-1 alpha-2 country code, e.g. `UA`."),
        OpenApiParameter("search", OpenApiTypes.STR,
                         description="Part of the city name, case-insensitive, e.g. `Київ`."),
    ],
)
class DeliveryCityListView(generics.ListAPIView):
    """
    Read-only city lookup for the checkout branch picker.

    Query params: provider (DeliveryProvider code), country (ISO alpha-2), search (name).
    """

    serializer_class = DeliveryCitySerializer
    pagination_class = DeliveryCityPagination

    def get_queryset(self):
        queryset = DeliveryCity.objects.all()

        provider = self.request.query_params.get("provider")
        if provider:
            queryset = queryset.filter(provider=provider)

        country = self.request.query_params.get("country")
        if country:
            queryset = queryset.filter(country=country)

        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(name__icontains=search).annotate(
                rank=Case(
                    When(name__iexact=search, then=Value(0)),
                    When(name__istartswith=search, then=Value(1)),
                    default=Value(2),
                    output_field=IntegerField(),
                )
            )
            return queryset.order_by("rank", "name")

        return queryset.order_by("name")


@extend_schema(
    tags=["delivery"],
    summary="List branches of a city",
    description="Paginated, `limit` up to 50 (50 by default), in alphabetical order. Without `city` every branch of every city "
                "is returned, so the checkout always passes it.",
    parameters=[
        OpenApiParameter("city", OpenApiTypes.INT,
                         description="City `id` from the cities endpoint (not the provider's ref)."),
        OpenApiParameter("search", OpenApiTypes.STR,
                         description="Part of the branch name, case-insensitive, e.g. `Відділення №1`."),
    ],
)
class DeliveryBranchListView(generics.ListAPIView):
    """
    Read-only branch lookup within a chosen city, for the checkout branch picker.

    Query params: city (DeliveryCity id, required to get useful results), search (name).
    """

    serializer_class = DeliveryBranchSerializer
    pagination_class = DeliveryBranchPagination
    def get_queryset(self):
        queryset = DeliveryBranch.objects.all()

        city_id = self.request.query_params.get("city")
        if city_id:
            queryset = queryset.filter(city_id=city_id)

        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset.order_by("name")
