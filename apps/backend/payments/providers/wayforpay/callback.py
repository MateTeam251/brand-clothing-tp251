from django.utils import timezone
from decimal import Decimal

from django.db import transaction

from orders.models import OrderStatus
from payments.models import Payment, PaymentProvider, PaymentStatus
from payments.providers.wayforpay.config import get_wayforpay_config
from payments.providers.wayforpay.signatures import (
    verify_signature,
    build_callback_response_signature,
    build_callback_signature,
)


def handle_callback(data: dict) -> dict:
    config = get_wayforpay_config()

    required_fields = (
        "merchantAccount",
        "orderReference",
        "merchantSignature",
        "amount",
        "currency",
        "authCode",
        "cardPan",
        "transactionStatus",
        "reasonCode",
    )

    missing_fields = [field for field in required_fields if field not in data]

    if missing_fields:
        raise ValueError(
            f"Missing required callback fields: {', '.join(missing_fields)}"
        )

    if data["merchantAccount"] != config.merchant_account:
        raise ValueError("Invalid merchant account")

    expected_signature = build_callback_signature(
        merchant_account=data["merchantAccount"],
        order_reference=data["orderReference"],
        amount=data["amount"],
        currency=data["currency"],
        auth_code=data["authCode"],
        card_pan=data["cardPan"],
        transaction_status=data["transactionStatus"],
        reason_code=data["reasonCode"],
        secret_key=config.secret_key,
    )

    is_valid_signature = verify_signature(
        received_signature=data["merchantSignature"],
        expected_signature=expected_signature,
    )

    if not is_valid_signature:
        raise ValueError("Invalid WayForPay callback signature")

    try:
        with transaction.atomic():
            payment = (
                Payment.objects
                .select_for_update()
                .select_related("order")
                .get(
                    provider=PaymentProvider.WAYFORPAY,
                    provider_order_reference=data["orderReference"],
                )
            )

            if Decimal(str(data["amount"])) != payment.amount:
                raise ValueError("Payment amount does not match")

            if data["currency"] != payment.currency:
                raise ValueError("Payment currency does not match")

            if payment.status != PaymentStatus.SUCCESSFUL:
                transaction_status = data["transactionStatus"]

                if transaction_status == "Approved":
                    payment.status = PaymentStatus.SUCCESSFUL
                    payment.transaction_id = data["authCode"]
                    payment.paid_at = timezone.now()

                    payment.payment_data = {
                        **payment.payment_data,
                        "reason_code": data["reasonCode"],
                        "transaction_status": transaction_status,
                        "payment_system": data.get("paymentSystem", ""),
                    }

                    payment.order.status = OrderStatus.PAID
                    payment.order.save(update_fields=["status", "updated_at"])

                    payment.save(
                        update_fields=[
                            "status",
                            "transaction_id",
                            "paid_at",
                            "payment_data",
                            "updated_at",
                        ]
                    )
    except Payment.DoesNotExist:
        raise ValueError(f"Payment with reference {data['orderReference']} not found")

    response_time = int(timezone.now().timestamp())
    response_status = "accept"

    response_signature = build_callback_response_signature(
        order_reference=data["orderReference"],
        status=response_status,
        timestamp=response_time,
        secret_key=config.secret_key,
    )

    return {
        "orderReference": data["orderReference"],
        "status": response_status,
        "time": response_time,
        "signature": response_signature,
    }
