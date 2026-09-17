from rest_framework import (viewsets,
                            filters)
from products.serializers import (ProductListSerializer,
                                  ProductDetailSerializer,
                                  CollectionSerializer,
                                  CollectionDetailSerializer)
from products.models import Product, Collection
from django.db.models import F, Case, When, DecimalField, ExpressionWrapper


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


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Basic ViewSet with ReadOnlyMode

    Has name search field and ordering via price (uah and usd),
    created_at (auto incremented time stamp in Product model. Depends on when was the product add to the db)
    is_bestseller (bool) and is_new_collection (bool).
    Basic ordering depends on when was the product add to the db (so the new products are shown first)

    """
    queryset = Product.objects.all()
    filter_backends =  [filters.SearchFilter, CurrencyAwareOrderingFilter]

    search_fields = ["name"]
    ordering_fields = [
        "price", # resolved to price_auh/price_usd basen on ?currency=
        "created_at",
        "is_bestseller",
        "is_new_collection",
    ]
    ordering = ["-created_at"] #default sorting if the user didn't specify ordering

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer
        return ProductDetailSerializer

    def get_queryset(self):
        queryset = Product.objects.all()

        collection_slugs = self.request.query_params.get("collection")
        if collection_slugs:
            slugs = [slug.strip() for slug in collection_slugs.split(",") if slug.strip()]
            queryset = queryset.filter(collection__slug__in=slugs)

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
            return Collection.objects.prefetch_related("products__images")
        return Collection.objects.all()
