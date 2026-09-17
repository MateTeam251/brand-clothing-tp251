import requests

from payments.providers.wayforpay.config import get_wayforpay_config
from payments.providers.wayforpay.signatures import build_purchase_signature


def build_purchase_payload(
        *,
        order_reference: str,
        order_date: int,
        amount: str,
        currency: str,
        product_names: list[str],
        product_counts: list[str],
        product_prices: list[str],
        language: str = "UA"
) -> dict:
    """
    Creating a payload for a Purchase request in WayForPay.

    The payload complies with the parameters required by the WayForPay Purchase API.
    """

    if not (len(product_names) == len(product_counts) == len(product_prices)):
        raise ValueError(
            "product_names, product_counts and product_prices must have the same length"
        )

    config = get_wayforpay_config()

    merchant_signature = build_purchase_signature(
        merchant_account=config.merchant_account,
        merchant_domain=config.merchant_domain,
        order_reference=order_reference,
        order_date=order_date,
        amount=amount,
        currency=currency,
        product_names=product_names,
        product_counts=product_counts,
        product_prices=product_prices,
        secret_key=config.secret_key,
    )

    return {
        "merchantAccount": config.merchant_account,
        "merchantDomainName": config.merchant_domain,
        "merchantTransactionType": "AUTO",
        "merchantTransactionSecureType": "AUTO",
        "merchantSignature": merchant_signature,
        "apiVersion": 2,
        "language": language,
        "returnUrl": config.return_url,
        "serviceUrl": config.service_url,
        "orderReference": order_reference,
        "orderDate": order_date,
        "amount": amount,
        "currency": currency,
        "productName[]": product_names,
        "productCount[]": product_counts,
        "productPrice[]": product_prices,
    }


def send_purchase_request(
        *,
        order_reference: str,
        order_date: int,
        amount: str,
        currency: str,
        product_names: list[str],
        product_counts: list[str],
        product_prices: list[str],
        language: str = "UA"
) -> str:
    """
    Creates and sends a signed purchase Request to WayForPay and returns its response.
    """

    payload = build_purchase_payload(
        order_reference=order_reference,
        order_date=order_date,
        amount=amount,
        currency=currency,
        product_names=product_names,
        product_counts=product_counts,
        product_prices=product_prices,
        language=language
    )

    config = get_wayforpay_config()

    form_data = []

    for key, value in payload.items():
        if isinstance(value, list):
            for item in value:
                form_data.append((key, str(item)))
        else:
            form_data.append((key, str(value)))

    response = requests.post(
        f"{config.api_url}?behavior=offline",
        data=form_data,
        timeout=(5, 15)
    )
    response.raise_for_status()

    response_data = response.json()

    payment_url = response_data.get("url")

    if not payment_url:
        raise ValueError(
            f"WayForPay did not return payment URL: "
            f"{response_data.get('reason', 'Unknown error')}"
        )

    return payment_url
