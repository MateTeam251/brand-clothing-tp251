from rest_framework import (viewsets,
                            filters)
from products.serializers import (ProductListSerializer,
                                  ProductDetailSerializer, CollectionSerializer, CollectionDetailSerializer)
from products.models import Product, Collection




class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Basic ViewSet with ReadOnlyMode

    Has name search field and ordering via price (uah and usd),
    created_at (auto incremented time stamp in Product model. Depends on when was the product add to the db)
    is_bestseller (bool) and is_new_collection (bool).
    Basic ordering depends on when was the product add to the db (so the new products are shown first)

    """
    queryset = Product.objects.all()
    filter_backends =  [filters.SearchFilter, filters.OrderingFilter]

    search_fields = ["name"]
    ordering_fields = [
        "price_uah",
        "price_usd",
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
