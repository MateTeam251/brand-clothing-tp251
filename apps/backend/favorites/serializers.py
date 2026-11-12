from rest_framework import serializers
from favorites.models import Favorite
from products.serializers import ProductListSerializer



class FavoriteSerializer(serializers.ModelSerializer):
    product_details = ProductListSerializer(
        source="product", read_only=True, help_text="Product card, the same as in the catalog list.")

    class Meta:
        model = Favorite
        fields = ("id", "product", "product_details", "created_at")
        read_only_fields = ("id", "product_details", "created_at")
        extra_kwargs = {
            "id": {"help_text": "Favorite record id (not the product id)."},
            "product": {"help_text": "Product id."},
            "created_at": {"help_text": "When it was added, UTC."},
        }

    def validate_product(self, product):
        if product.is_archived:
            raise serializers.ValidationError("This product is archived.")
        return product


