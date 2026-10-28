from rest_framework import (viewsets,
                            filters, generics)
from rest_framework.permissions import AllowAny
from rest_framework.throttling import ScopedRateThrottle

from products.serializers import (ProductListSerializer,
                                  ProductDetailSerializer,
                                  CollectionSerializer,
                                  CollectionDetailSerializer, AvailabilityRequestSerializer)
from products.models import Product, Collection
from django.db.models import F, Case, When, DecimalField, ExpressionWrapper, Prefetch

from products.utils import send_availability_request_notification
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view

from core.openapi import CURRENCY_PARAM, LANG_PARAM, NOT_FOUND, THROTTLED, VALIDATION_ERROR


class CurrencyAwareOrderingFilter(filters.OrderingFilter):
    """
    Extends DRF's OrderingFilter so that ordering by "price" resolves to
    the correct underlying column (price_uah or price_usd) based on the
    same ?currency= query parameter used elsewhere (see CurrencyMixin).

    This keeps the public API consistent: clients always sort by "price",
    matching the "price" field they see in the serialized response,
    without needing to know about the price_uah/price_usd split.
    """

    def get_ordering(self, request, queryset, view):
        ordering = super().get_ordering(request, queryset, view)
        if not ordering:
            return ordering

        currency = request.query_params.get("currency", "uah")
        price_field = "effective_price_usd" if currency == "usd" else "effective_price_uah"

        return [
            ("-" if field.startswith("-") else "") + price_field
            if field.lstrip("-") == "price" else field
            for field in ordering
        ]


@extend_schema_view(
    list=extend_schema(
        summary="Product catalog",
        description="Paginated list of product cards. Archived products are never included. "
                    "Filters can be combined; an unknown slug in `collection`/`type` just gives an empty list.",
        parameters=[
            LANG_PARAM,
            CURRENCY_PARAM,
            OpenApiParameter("collection", OpenApiTypes.STR,
                             description="Collection slugs, comma-separated: `summer-2026,new-year`."),
            OpenApiParameter("type", OpenApiTypes.STR,
                             description="Product type slugs, comma-separated: `dress,skirt`."),
            OpenApiParameter("is_bestseller", OpenApiTypes.STR, enum=["true"],
                             description="`true` = bestsellers only. Any other value is ignored."),
            OpenApiParameter("search", OpenApiTypes.STR,
                             description="Part of the product name, case-insensitive."),
            OpenApiParameter("ordering", OpenApiTypes.STR,
                             enum=["price", "-price", "created_at", "-created_at"],
                             description="Sort order. `price` sorts by the price after discount in the "
                                         "`?currency=` currency. Default `-created_at` (newest first)."),
        ],
    ),
    retrieve=extend_schema(
        summary="Product page",
        description="Full product data: description, all photos, size guide. "
                    "An archived product gives 404, the same as a non-existent one.",
        parameters=[LANG_PARAM, CURRENCY_PARAM],
        responses={200: ProductDetailSerializer, 404: NOT_FOUND},
    ),
)
@extend_schema(tags=["products"])
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Basic ViewSet with ReadOnlyMode.

    Supports:
    - name search (?search=)
    - ordering by price (uah/usd via ?currency=) and created_at
    - filtering by collection (?collection=slug1,slug2)
    - filtering by product type (?type=slug1,slug2)
    - filtering to bestsellers only (?is_bestseller=true)

    Default ordering is by created_at descending (newest products first).
    Archived products are excluded from both list and retrieve.
    """
    filter_backends =  [filters.SearchFilter, CurrencyAwareOrderingFilter]

    search_fields = ["name"]
    ordering_fields = [
        "price", # resolved to price_auh/price_usd basen on ?currency=
        "created_at",
    ]
    ordering = ["-created_at"] #default sorting if the user didn't specify ordering

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer
        return ProductDetailSerializer

    def get_queryset(self):
        queryset = Product.objects.filter(is_archived=False)

        collection_slugs = self.request.query_params.get("collection")
        if collection_slugs:
            slugs = [slug.strip() for slug in collection_slugs.split(",") if slug.strip()]
            queryset = queryset.filter(collection__slug__in=slugs)

        type_slugs = self.request.query_params.get("type")
        if type_slugs:
            slugs = [s.strip() for s in type_slugs.split(",") if s.strip()]
            queryset = queryset.filter(type__slug__in=slugs)

        only_bestsellers = self.request.query_params.get("is_bestseller")
        if only_bestsellers == "true":
            queryset = queryset.filter(is_bestseller=True)


        queryset = queryset.annotate(
            effective_price_uah=Case(
                When(discount_percent__gt=0, then=ExpressionWrapper(
                    F("price_uah") * (1 - F("discount_percent") / 100.0),
                    output_field=DecimalField(max_digits=10, decimal_places=2),
                )),
                default=F("price_uah"),
                output_field=DecimalField(max_digits=10, decimal_places=2),
            ),
            effective_price_usd=Case(
                When(discount_percent__gt=0, then=ExpressionWrapper(
                    F("price_usd") * (1 - F("discount_percent") / 100.0),
                    output_field=DecimalField(max_digits=10, decimal_places=2),
                )),
                default=F("price_usd"),
                output_field=DecimalField(max_digits=10, decimal_places=2),
            ),
        )
        return queryset



@extend_schema_view(
    list=extend_schema(
        summary="Collections",
        description="Paginated list of collections, without their products.",
        parameters=[
            LANG_PARAM,
            OpenApiParameter("ordering", OpenApiTypes.STR, enum=["name", "-name", "id", "-id"],
                             description="Sort order. Without it the order is not guaranteed."),
            # SearchFilter is enabled but has no search_fields, so ?search= does nothing.
            OpenApiParameter("search", exclude=True),
        ],
    ),
    retrieve=extend_schema(
        summary="Collection page",
        description="One collection by its `slug`, with all its products (not paginated). "
                    "Archived products are not included.",
        parameters=[LANG_PARAM, CURRENCY_PARAM],
        responses={200: CollectionDetailSerializer, 404: NOT_FOUND},
    ),
)
@extend_schema(tags=["collections"])
class CollectionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Collection.objects.all()
    lookup_field = "slug"
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]


    def get_serializer_class(self):
        if self.action == "retrieve":
            return CollectionDetailSerializer
        return CollectionSerializer

    def get_queryset(self):
        if self.action == "retrieve":
            return Collection.objects.prefetch_related(
                Prefetch("products", queryset=Product.objects.filter(is_archived=False).prefetch_related("images"))
            )
        return Collection.objects.all()


@extend_schema(
    tags=["products"],
    summary="Ask about availability",
    description="\"Check availability\" form on a product that is out of stock (and not archived). No login needed. "
                "Saves the request for the manager (admin, Availability requests) and emails the manager.",
    responses={201: AvailabilityRequestSerializer, 400: VALIDATION_ERROR, 429: THROTTLED},
)
class AvailabilityRequestView(generics.CreateAPIView):
    """
    POST /api/products/availability-requests/
    Public endpoint — anyone (including guests) can submit a "notify me"
    request. Throttled to prevent spam/abuse.
    """
    serializer_class = AvailabilityRequestSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "availability_request"

    def perform_create(self, serializer):
        instance = serializer.save()
        send_availability_request_notification(instance)
