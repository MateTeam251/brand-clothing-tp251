from rest_framework import serializers

from delivery.models import DeliveryCity, DeliveryBranch


class DeliveryCitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryCity
        fields = ("id", "provider", "country", "name")
        read_only_fields = fields


class DeliveryBranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryBranch
        fields = ("id", "provider", "city", "name", "address", "postal_code")
        read_only_fields = fields
