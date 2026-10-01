from rest_framework import serializers

from payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            "id",
            "order",
            "currency",
            "amount",
            "provider",
            "status",
            "transaction_id",
            "paid_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class WayForPayCallbackSerializer(serializers.Serializer):
    merchantAccount = serializers.CharField()
    orderReference = serializers.CharField()
    merchantSignature = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField()
    authCode = serializers.CharField(required=False, allow_blank=True)
    cardPan = serializers.CharField(required=False, allow_blank=True)
    transactionStatus = serializers.CharField()
    reasonCode = serializers.CharField(required=False, allow_blank=True)
    paymentSystem = serializers.CharField(required=False, allow_blank=True)


class WayForPayCallbackResponseSerializer(serializers.Serializer):
    orderReference = serializers.CharField()
    status = serializers.CharField()
    time = serializers.IntegerField()
    signature = serializers.CharField()
