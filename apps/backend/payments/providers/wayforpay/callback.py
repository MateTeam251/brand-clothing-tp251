import logging
import requests
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from carts.models import CartStatusEnum
from core.enums import OrderStatus, PaymentStatus, PaymentProvider
from orders.email_services import send_order_paid_email
from orders.models import Order
from payments.models import Payment
from payments.providers.wayforpay.check_status import check_payment_status
from payments.providers.wayforpay.config import get_wayforpay_config
from payments.providers.wayforpay.signatures import (
    verify_signature,
    build_callback_response_signature,
    build_callback_signature,
)

logger = logging.getLogger(__name__)

_PAYMENT_DATA_FIELDS = {
    "transactionStatus": "transaction_status",
    "reason": "reason",
    "reasonCode": "reason_code",
    "paymentSystem": "payment_system",
    "cardType": "card_type",
    "cardPan": "card_pan",
    "issuerBankCountry": "issuer_bank_country",
    "issuerBankName": "issuer_bank_name",
    "acquirerBankName": "acquirer_bank_name",
    "fee": "fee",
    "createdDate": "created_date",
    "processingDate": "processing_date",
    "authCode": "auth_code",
}


def _build_payment_data(data: dict) -> dict:
    """
    Whitelist non-confidential provider fields
    (no recToken, no signature, no identifying information).
    """

    return {
        our_key: data[wfp_key]
        for wfp_key, our_key in _PAYMENT_DATA_FIELDS.items()
        if wfp_key in data
    }


def _apply_payment_result(data: dict) -> None:
    """
    Applies an already verified WayForPay result (callback or status check)
    to the payment and its order. Idempotent: safe to call repeatedly.

    Must be called inside transaction.atomic().
    Order locking always occurs in the payment -> order pattern,
    so concurrent calls cannot cause deadlocks.
    """

    payment = (
        Payment.objects
        .select_for_update()
        .get(
            provider=PaymentProvider.WAYFORPAY,
            provider_order_reference=data["orderReference"],
        )
    )

    if Decimal(str(data["amount"])) != payment.amount:
        raise ValueError("Payment amount does not match")

    if data["currency"] != payment.currency:
        raise ValueError("Payment currency does not match")

    transaction_status = data["transactionStatus"]
    payment_data = {
        **payment.payment_data,
        **_build_payment_data(data),
    }

    if transaction_status == "Approved":
        order = Order.objects.select_for_update().get(pk=payment.order_id)

        if payment.status == PaymentStatus.DUPLICATE:
            return

        if payment.status != PaymentStatus.SUCCESSFUL and order.status == OrderStatus.CANCELED:
            payment.status = PaymentStatus.DUPLICATE
            payment.paid_at = timezone.now()
            payment.payment_data = {
                **payment_data,
                "needs_refund": True,
                "refund_reason": "order_canceled",
            }

            payment.save(
                update_fields=[
                    "status",
                    "paid_at",
                    "payment_data",
                    "updated_at",
                ]
            )

            logger.error(
                "Payment for canceled order, refund required: order=%s payment=%s",
                order.order_reference,
                payment.provider_order_reference,
            )
            return

        if payment.status != PaymentStatus.SUCCESSFUL:
            already_paid = (
                Payment.objects
                .filter(order=order, status=PaymentStatus.SUCCESSFUL)
                .exclude(pk=payment.pk)
                .exists()
            )

            if already_paid:
                payment.status = PaymentStatus.DUPLICATE
                payment.paid_at = timezone.now()

                payment.payment_data = {
                    **payment_data,
                    "needs_refund": True,
                }

                payment.save(
                    update_fields=[
                        "status",
                        "paid_at",
                        "payment_data",
                        "updated_at",
                    ]
                )

                logger.error(
                    "Duplicate successful payment, refund required: order=%s payment=%s",
                    order.order_reference,
                    payment.provider_order_reference,
                )
                return

            payment.status = PaymentStatus.SUCCESSFUL
            payment.paid_at = timezone.now()
            payment.payment_data = payment_data

            payment.save(
                update_fields=[
                    "status",
                    "paid_at",
                    "payment_data",
                    "updated_at",
                ]
            )

        if order.status != OrderStatus.PAID:
            order.status = OrderStatus.PAID
            order.save(update_fields=["status", "updated_at"])

            if order.cart and order.cart.status == CartStatusEnum.ACTIVE:
                order.cart.mark_converted()

            transaction.on_commit(lambda: send_order_paid_email(order), robust=True)

    elif transaction_status in ("Declined", "Expired"):
        if payment.status == PaymentStatus.PENDING:
            payment.status = PaymentStatus.FAILED
            payment.payment_data = payment_data

            payment.save(
                update_fields=[
                    "status",
                    "payment_data",
                    "updated_at",
                ]
            )
    else:
        logger.info(
            "Unhandled WayForPay status %s for %s",
            transaction_status,
            data["orderReference"],
        )


def handle_callback(data: dict) -> dict:
    config = get_wayforpay_config()

    required_fields = (
        "merchantAccount",
        "orderReference",
        "merchantSignature",
        "amount",
        "currency",
        "transactionStatus",
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
        auth_code=data.get("authCode"),
        card_pan=data.get("cardPan"),
        transaction_status=data["transactionStatus"],
        reason_code=data.get("reasonCode"),
        secret_key=config.secret_key,
    )

    if not verify_signature(
        received_signature=data["merchantSignature"],
        expected_signature=expected_signature,
    ):
        raise ValueError("Invalid WayForPay callback signature")

    try:
        with transaction.atomic():
            _apply_payment_result(data)
    except Payment.DoesNotExist:
        raise ValueError(f"Payment with reference {data['orderReference']} not found")
    except Order.DoesNotExist:
        raise ValueError(f"Order for payment {data['orderReference']} not found")

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


def sync_payment_status(payment: Payment) -> Payment:
    """
    Asks WayForPay for the actual status of the payment attempt and applies it.
    """

    try:
        data = check_payment_status(payment.provider_order_reference)
        with transaction.atomic():
            _apply_payment_result(data)
    except (requests.RequestException, ValueError):
        logger.warning(
            "Check Status failed for %s",
            payment.provider_order_reference,
            exc_info=True,
        )

    payment.refresh_from_db()
    return payment
