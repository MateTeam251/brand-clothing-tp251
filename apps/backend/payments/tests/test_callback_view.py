from decimal import Decimal

import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from orders.models import Order, OrderStatus
from payments.models import Payment, PaymentProvider, PaymentStatus
from payments.providers.wayforpay.signatures import (
    build_callback_response_signature,
    build_callback_signature,
)


TEST_SECRET_KEY = "test-secret-key"

@pytest.fixture
def wayforpay_settings():
    with override_settings(
        WAYFORPAY_MERCHANT_ACCOUNT="test_merchant",
        WAYFORPAY_SECRET_KEY=TEST_SECRET_KEY,
        WAYFORPAY_MERCHANT_DOMAIN="www.market.ua",
        WAYFORPAY_SERVICE_URL=(
            "https://market.ua/api/payments/wayforpay/callback/"
        ),
        WAYFORPAY_RETURN_URL="https://market.ua/payment/success/",
        WAYFORPAY_API_URL="https://secure.wayforpay.com/pay",
        WAYFORPAY_CHECK_STATUS_URL="https://api.wayforpay.com/api",
    ):
        yield


@pytest.fixture
def payment():
    order = Order.objects.create(
        delivery_address="Test address",
        email="test@example.com",
        status=OrderStatus.CREATED,
        currency="UAH",
        subtotal=Decimal("100.00"),
        discount_amount=Decimal("0.00"),
        delivery_cost=Decimal("0.00"),
        total_amount=Decimal("100.00"),
        delivery_provider="NOVA_POSHTA",
        user_name="Test User",
        user_phone="+380991234567",
    )

    return Payment.objects.create(
        order=order,
        currency="UAH",
        amount=Decimal("100.00"),
        provider=PaymentProvider.WAYFORPAY,
        status=PaymentStatus.PENDING,
        provider_order_reference="ORDER-123",
    )


@pytest.fixture
def callback_data():
    data = {
        "merchantAccount": "test_merchant",
        "orderReference": "ORDER-123",
        "amount": "100.00",
        "currency": "UAH",
        "authCode": "123456",
        "cardPan": "123456******1234",
        "transactionStatus": "Approved",
        "reasonCode": 1100,
        "paymentSystem": "card",
    }

    data["merchantSignature"] = build_callback_signature(
        merchant_account=data["merchantAccount"],
        order_reference=data["orderReference"],
        amount=data["amount"],
        currency=data["currency"],
        auth_code=data["authCode"],
        card_pan=data["cardPan"],
        transaction_status=data["transactionStatus"],
        reason_code=data["reasonCode"],
        secret_key=TEST_SECRET_KEY,
    )

    return data


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_wayforpay_callback_returns_success_response(
    api_client,
    payment,
    callback_data,
    wayforpay_settings,
):
    response = api_client.post(
        "/api/payments/wayforpay/callback/",
        callback_data,
        format="json",
    )

    assert response.status_code == 200

    assert response.data["orderReference"] == "ORDER-123"
    assert response.data["status"] == "accept"
    assert "time" in response.data
    assert "signature" in response.data


@pytest.mark.django_db
def test_wayforpay_callback_processes_payment(
    api_client,
    payment,
    callback_data,
    wayforpay_settings,
):
    response = api_client.post(
        "/api/payments/wayforpay/callback/",
        callback_data,
        format="json",
    )

    assert response.status_code == 200

    payment.refresh_from_db()
    payment.order.refresh_from_db()

    assert payment.status == PaymentStatus.SUCCESSFUL
    assert payment.transaction_id == "123456"
    assert payment.paid_at is not None
    assert payment.order.status == OrderStatus.PAID


@pytest.mark.django_db
def test_wayforpay_callback_returns_valid_response_signature(
    api_client,
    payment,
    callback_data,
    wayforpay_settings,
):
    response = api_client.post(
        "/api/payments/wayforpay/callback/",
        callback_data,
        format="json",
    )

    assert response.status_code == 200

    expected_signature = build_callback_response_signature(
        order_reference="ORDER-123",
        status="accept",
        timestamp=response.data["time"],
        secret_key=TEST_SECRET_KEY,
    )

    assert response.data["signature"] == expected_signature


@pytest.mark.django_db
def test_wayforpay_callback_rejects_invalid_signature(
    api_client,
    payment,
    callback_data,
    wayforpay_settings,
):
    callback_data["merchantSignature"] = "invalid-signature"

    response = api_client.post(
        "/api/payments/wayforpay/callback/",
        callback_data,
        format="json",
    )

    assert response.status_code == 400
    assert "Invalid WayForPay callback signature" in response.data["detail"]

    payment.refresh_from_db()

    assert payment.status == PaymentStatus.PENDING


@pytest.mark.django_db
def test_wayforpay_callback_rejects_unknown_payment(
    api_client,
    callback_data,
    wayforpay_settings,
):
    callback_data["orderReference"] = "UNKNOWN-ORDER"

    callback_data["merchantSignature"] = build_callback_signature(
        merchant_account=callback_data["merchantAccount"],
        order_reference=callback_data["orderReference"],
        amount=callback_data["amount"],
        currency=callback_data["currency"],
        auth_code=callback_data["authCode"],
        card_pan=callback_data["cardPan"],
        transaction_status=callback_data["transactionStatus"],
        reason_code=callback_data["reasonCode"],
        secret_key=TEST_SECRET_KEY,
    )

    response = api_client.post(
        "/api/payments/wayforpay/callback/",
        callback_data,
        format="json",
    )

    assert response.status_code == 400
    assert "not found" in response.data["detail"]


@pytest.mark.django_db
def test_wayforpay_callback_rejects_amount_mismatch(
    api_client,
    payment,
    callback_data,
    wayforpay_settings,
):
    callback_data["amount"] = "200.00"

    callback_data["merchantSignature"] = build_callback_signature(
        merchant_account=callback_data["merchantAccount"],
        order_reference=callback_data["orderReference"],
        amount=callback_data["amount"],
        currency=callback_data["currency"],
        auth_code=callback_data["authCode"],
        card_pan=callback_data["cardPan"],
        transaction_status=callback_data["transactionStatus"],
        reason_code=callback_data["reasonCode"],
        secret_key=TEST_SECRET_KEY,
    )

    response = api_client.post(
        "/api/payments/wayforpay/callback/",
        callback_data,
        format="json",
    )

    assert response.status_code == 400
    assert response.data["detail"] == "Payment amount does not match"


@pytest.mark.django_db
def test_wayforpay_callback_rejects_missing_field(
    api_client,
    payment,
    callback_data,
    wayforpay_settings,
):
    callback_data.pop("amount")

    response = api_client.post(
        "/api/payments/wayforpay/callback/",
        callback_data,
        format="json",
    )

    assert response.status_code == 400
    assert "amount" in response.data["detail"]


@pytest.mark.django_db
def test_wayforpay_callback_rejects_get_request(
    api_client,
    wayforpay_settings,
):
    response = api_client.get(
        "/api/payments/wayforpay/callback/",
    )

    assert response.status_code == 405


@pytest.mark.django_db
def test_wayforpay_callback_is_idempotent(
    api_client,
    payment,
    callback_data,
    wayforpay_settings,
):
    first_response = api_client.post(
        "/api/payments/wayforpay/callback/",
        callback_data,
        format="json",
    )

    payment.refresh_from_db()
    first_paid_at = payment.paid_at
    first_transaction_id = payment.transaction_id

    second_response = api_client.post(
        "/api/payments/wayforpay/callback/",
        callback_data,
        format="json",
    )

    payment.refresh_from_db()

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    assert payment.status == PaymentStatus.SUCCESSFUL
    assert payment.paid_at == first_paid_at
    assert payment.transaction_id == first_transaction_id
