import pytest
from django.test import override_settings

from orders.models import Order, OrderStatus
from payments.models import Payment, PaymentProvider, PaymentStatus
from payments.providers.wayforpay.callback import handle_callback
from payments.providers.wayforpay.signatures import (
    build_callback_signature,
    build_callback_response_signature,
)

TEST_SECRET_KEY = "test-secret-key"


@pytest.fixture
def wayforpay_settings():
    with override_settings(
        WAYFORPAY_MERCHANT_ACCOUNT="test_merchant",
        WAYFORPAY_SECRET_KEY=TEST_SECRET_KEY,
        WAYFORPAY_MERCHANT_DOMAIN="www.market.ua",
        WAYFORPAY_SERVICE_URL="https://market.ua/api/payments/wayforpay/callback/",
        WAYFORPAY_RETURN_URL="https://market.ua/payment/success/",
        WAYFORPAY_API_URL="https://secure.wayforpay.com/pay",
        WAYFORPAY_CHECK_STATUS_URL="https://api.wayforpay.com/api",
    ):
        yield


@pytest.fixture
def payment():
    order = Order.objects.create(
        user_name="User 1",
        user_phone="+380991234567",
        email="user1@test.com",
        delivery_address="Kyiv, Ukraine",
        currency="UAH",
        subtotal="100.00",
        discount_amount="0.00",
        delivery_cost="0.00",
        total_amount="100.00",
        delivery_provider="NOVA_POSHTA",
        status=OrderStatus.CREATED,
    )

    return Payment.objects.create(
        order=order,
        currency="UAH",
        amount="100.00",
        provider=PaymentProvider.WAYFORPAY,
        status=PaymentStatus.PENDING,
        provider_order_reference="ORDER-123",
    )


def build_callback_data(
    *,
    amount="100.00",
    currency="UAH",
    transaction_status="Approved",
):
    merchant_account = "test_merchant"
    order_reference = "ORDER-123"
    auth_code = "123456"
    card_pan = "414141******1111"
    reason_code = "1100"

    signature = build_callback_signature(
        merchant_account=merchant_account,
        order_reference=order_reference,
        amount=amount,
        currency=currency,
        auth_code=auth_code,
        card_pan=card_pan,
        transaction_status=transaction_status,
        reason_code=reason_code,
        secret_key=TEST_SECRET_KEY,
    )

    return {
        "merchantAccount": merchant_account,
        "orderReference": order_reference,
        "merchantSignature": signature,
        "amount": amount,
        "currency": currency,
        "authCode": auth_code,
        "cardPan": card_pan,
        "transactionStatus": transaction_status,
        "reasonCode": reason_code,
    }


def build_declined_callback_data_with_none():
    merchant_account = "test_merchant"
    order_reference = "ORDER-123"
    amount = "100.00"
    currency = "UAH"
    auth_code = None
    card_pan = "414141******1111"
    transaction_status = "Declined"
    reason_code = None

    signature = build_callback_signature(
        merchant_account=merchant_account,
        order_reference=order_reference,
        amount=amount,
        currency=currency,
        auth_code=auth_code,
        card_pan=card_pan,
        transaction_status=transaction_status,
        reason_code=reason_code,
        secret_key=TEST_SECRET_KEY,
    )

    return {
        "merchantAccount": merchant_account,
        "orderReference": order_reference,
        "merchantSignature": signature,
        "amount": amount,
        "currency": currency,
        "authCode": auth_code,
        "cardPan": card_pan,
        "transactionStatus": transaction_status,
        "reasonCode": reason_code,
    }


@pytest.mark.django_db
def test_handle_successful_callback(
        payment,
        wayforpay_settings
):
    data = build_callback_data()

    response = handle_callback(data)

    payment.refresh_from_db()
    payment.order.refresh_from_db()

    assert payment.status == PaymentStatus.SUCCESSFUL
    assert payment.transaction_id == "123456"
    assert payment.paid_at is not None
    assert payment.order.status == OrderStatus.PAID

    assert response["orderReference"] == "ORDER-123"
    assert response["status"] == "accept"
    assert "time" in response
    assert "signature" in response


@pytest.mark.django_db
def test_handle_callback_rejects_invalid_signature(
    payment,
    wayforpay_settings,
):
    data = build_callback_data()
    data["merchantSignature"] = "invalid-signature"

    with pytest.raises(
        ValueError,
        match="Invalid WayForPay callback signature",
    ):
        handle_callback(data)

    payment.refresh_from_db()
    payment.order.refresh_from_db()

    assert payment.status == PaymentStatus.PENDING
    assert payment.paid_at is None
    assert payment.order.status == OrderStatus.CREATED


@pytest.mark.django_db
def test_handle_callback_rejects_amount_mismatch(
    payment,
    wayforpay_settings,
):
    data = build_callback_data(amount="200.00")

    with pytest.raises(
        ValueError,
        match="Payment amount does not match",
    ):
        handle_callback(data)

    payment.refresh_from_db()
    payment.order.refresh_from_db()

    assert payment.status == PaymentStatus.PENDING
    assert payment.paid_at is None
    assert payment.order.status == OrderStatus.CREATED


@pytest.mark.django_db
def test_handle_callback_rejects_currency_mismatch(
    payment,
    wayforpay_settings,
):
    data = build_callback_data(currency="USD")

    with pytest.raises(
        ValueError,
        match="Payment currency does not match",
    ):
        handle_callback(data)

    payment.refresh_from_db()
    payment.order.refresh_from_db()

    assert payment.status == PaymentStatus.PENDING
    assert payment.paid_at is None
    assert payment.order.status == OrderStatus.CREATED


@pytest.mark.django_db
def test_handle_duplicate_successful_callback(
    payment,
    wayforpay_settings,
):
    data = build_callback_data()

    handle_callback(data)

    payment.refresh_from_db()

    first_paid_at = payment.paid_at
    first_transaction_id = payment.transaction_id

    handle_callback(data)

    payment.refresh_from_db()

    assert payment.status == PaymentStatus.SUCCESSFUL
    assert payment.paid_at == first_paid_at
    assert payment.transaction_id == first_transaction_id


@pytest.mark.django_db
def test_handle_callback_rejects_missing_required_field(
    payment,
    wayforpay_settings,
):
    data = build_callback_data()
    del data["reasonCode"]

    with pytest.raises(
        ValueError,
        match="Missing required callback fields: reasonCode",
    ):
        handle_callback(data)

    payment.refresh_from_db()

    assert payment.status == PaymentStatus.PENDING


@pytest.mark.django_db
def test_handle_callback_rejects_invalid_merchant_account(
    payment,
    wayforpay_settings,
):
    data = build_callback_data()
    data["merchantAccount"] = "another_merchant"

    with pytest.raises(
        ValueError,
        match="Invalid merchant account",
    ):
        handle_callback(data)

    payment.refresh_from_db()

    assert payment.status == PaymentStatus.PENDING


@pytest.mark.django_db
def test_handle_callback_rejects_unknown_payment(
    wayforpay_settings,
):
    data = build_callback_data()

    with pytest.raises(
        ValueError,
        match="Payment with reference ORDER-123 not found",
    ):
        handle_callback(data)


@pytest.mark.django_db
def test_handle_callback_with_none_fields_validates_signature(
    payment,
    wayforpay_settings,
):
    data = build_declined_callback_data_with_none()

    response = handle_callback(data)

    payment.refresh_from_db()
    payment.order.refresh_from_db()

    assert payment.status == PaymentStatus.PENDING
    assert payment.order.status == OrderStatus.CREATED
    assert payment.paid_at is None

    assert response["status"] == "accept"
    assert response["orderReference"] == "ORDER-123"


@pytest.mark.django_db
def test_handle_callback_response_signature_is_valid(
    payment,
    wayforpay_settings,
):
    data = build_callback_data()

    response = handle_callback(data)

    expected_response_signature = build_callback_response_signature(
        order_reference=response["orderReference"],
        status=response["status"],
        timestamp=response["time"],
        secret_key=TEST_SECRET_KEY,
    )

    assert response["signature"] == expected_response_signature
