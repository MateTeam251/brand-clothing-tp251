import requests

from payments.providers.wayforpay.config import get_wayforpay_config
from payments.providers.wayforpay.signatures import (
    build_check_status_signature,
    build_check_status_response_signature,
    verify_signature,
)


def check_payment_status(order_reference: str) -> dict:
    config = get_wayforpay_config()

    signature = build_check_status_signature(
        merchant_account=config.merchant_account,
        order_reference=order_reference,
        secret_key=config.secret_key,
    )

    payload = {
        "transactionType": "CHECK_STATUS",
        "merchantAccount": config.merchant_account,
        "orderReference": order_reference,
        "merchantSignature": signature,
        "apiVersion": 1,
    }

    response = requests.post(
        config.check_status_url,
        json=payload,
        timeout=(5, 15),
    )

    response.raise_for_status()

    response_data = response.json()

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

    missing_fields = [field for field in required_fields if field not in response_data]

    if missing_fields:
        raise ValueError(
            f"Missing required WayForPay Check Status response fields: {', '.join(missing_fields)}"
        )

    if response_data["merchantAccount"] != config.merchant_account:
        raise ValueError("Invalid merchant account")

    if response_data["orderReference"] != order_reference:
        raise ValueError("Invalid order reference")

    expected_signature = build_check_status_response_signature(
        merchant_account=response_data["merchantAccount"],
        order_reference=response_data["orderReference"],
        amount=response_data["amount"],
        currency=response_data["currency"],
        auth_code=response_data["authCode"],
        card_pan=response_data["cardPan"],
        transaction_status=response_data["transactionStatus"],
        reason_code=response_data["reasonCode"],
        secret_key=config.secret_key,
    )

    is_valid_signature = verify_signature(
        received_signature=response_data["merchantSignature"],
        expected_signature=expected_signature,
    )

    if not is_valid_signature:
        raise ValueError("Invalid WayForPay Check Status signature")

    return response_data
