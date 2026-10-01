from rest_framework import serializers
from favorites.models import Favorite
from products.serializers import ProductListSerializer



class FavoriteSerializer(serializers.ModelSerializer):
    product_details = ProductListSerializer(source="product", read_only=True)

    class Meta:
        model = Favorite
        fields = ("id", "product", "product_details", "created_at")
        read_only_fields = ("id", "product_details", "created_at")


