import hashlib
import hmac


def _build_signature(*parts: object, secret_key: str) -> str:
    """
    Creating a WayForPay HMAC-MD5 signature.

    WayForPay requires:
    - parameters, separated by the ";" character
    - UTF-8 encoding
    - HMAC-MD5
    - merchant SecretKey
    """

    signature_string = ";".join(str(part) for part in parts)

    return hmac.new(
        secret_key.encode("utf-8"),
        signature_string.encode("utf-8"),
        hashlib.md5,
    ).hexdigest()


def build_purchase_signature(
        *,
        merchant_account: str,
        merchant_domain: str,
        order_reference: str,
        order_date: int,
        amount: str,
        currency: str,
        product_names: list[str],
        product_counts: list[str],
        product_prices: list[str],
        secret_key: str,
) -> str:
    """
    Generating a merchant signature for a Purchase request.

    WayForPay signature order:

    merchantAccount;
    merchantDomainName;
    orderReference;
    orderDate;
    amount;
    currency;
    productName[0..n];
    productCount[0..n];
    productPrice[0..n]
    """

    return _build_signature(
        merchant_account,
        merchant_domain,
        order_reference,
        order_date,
        amount,
        currency,
        *product_names,
        *product_counts,
        *product_prices,
        secret_key=secret_key,
    )


def build_callback_signature(
        *,
        merchant_account: str,
        order_reference: str,
        amount: str,
        currency: str,
        auth_code: str,
        card_pan: str,
        transaction_status: str,
        reason_code: str,
        secret_key: str,
) -> str:
    """
    Generating the expected merchant signature for the serviceUrl
    callback between WayForPay servers.

    WayForPay signature order:

    merchantAccount;
    orderReference;
    amount;
    currency;
    authCode;
    cardPan;
    transactionStatus;
    reasonCode
    """

    return _build_signature(
        merchant_account,
        order_reference,
        amount,
        currency,
        auth_code,
        card_pan,
        transaction_status,
        reason_code,
        secret_key=secret_key,
    )


def build_callback_response_signature(
        *,
        order_reference: str,
        status: str,
        timestamp: int,
        secret_key: str,
) -> str:
    """
    Generating a signature for the response sent by our server
    to WayForPay after processing the serviceUrl callback.

    WayForPay signature order:

    orderReference;
    status;
    time
    """

    return _build_signature(
        order_reference,
        status,
        timestamp,
        secret_key=secret_key,
    )


def build_check_status_signature(
        *,
        merchant_account: str,
        order_reference: str,
        secret_key: str,
) -> str:
    """
    Creating a merchant signature for a Check Status request.

    WayForPay signature order:

    merchantAccount;
    orderReference
    """

    return _build_signature(
        merchant_account,
        order_reference,
        secret_key=secret_key,
    )


def build_check_status_response_signature(
        *,
        merchant_account: str,
        order_reference: str,
        amount: str,
        currency: str,
        auth_code: str,
        card_pan: str,
        transaction_status: str,
        reason_code: str,
        secret_key: str,
) -> str:
    """
    Generating the expected merchant signature for the Check Status response.

    WayForPay signature order:

    merchantAccount;
    orderReference;
    amount;
    currency;
    authCode;
    cardPan;
    transactionStatus;
    reasonCode
    """

    return _build_signature(
        merchant_account,
        order_reference,
        amount,
        currency,
        auth_code,
        card_pan,
        transaction_status,
        reason_code,
        secret_key=secret_key,
    )


def verify_signature(
        *,
        received_signature: str,
        expected_signature: str,
) -> bool:
    return hmac.compare_digest(received_signature, expected_signature)
