from rest_framework import generics

from delivery.models import DeliveryCity, DeliveryBranch
from delivery.serializers import DeliveryCitySerializer, DeliveryBranchSerializer


class DeliveryCityListView(generics.ListAPIView):
    """
    Read-only city lookup for the checkout branch picker.

    Query params: provider (DeliveryProvider code), country (ISO alpha-2), search (name).
    """

    serializer_class = DeliveryCitySerializer

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
            queryset = queryset.filter(name__icontains=search)

        return queryset.order_by("name")


class DeliveryBranchListView(generics.ListAPIView):
    """
    Read-only branch lookup within a chosen city, for the checkout branch picker.

    Query params: city (DeliveryCity id, required to get useful results), search (name).
    """

    serializer_class = DeliveryBranchSerializer

    def get_queryset(self):
        queryset = DeliveryBranch.objects.all()

        city_id = self.request.query_params.get("city")
        if city_id:
            queryset = queryset.filter(city_id=city_id)

        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset.order_by("name")
