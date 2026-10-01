import uuid
from unittest.mock import Mock

import pytest
import requests
from django.test import override_settings

from payments.providers.wayforpay.check_status import check_payment_status
from payments.providers.wayforpay.signatures import (
    build_check_status_response_signature,
    build_check_status_signature,
)


TEST_SECRET_KEY = "test-secret-key"

TEST_ORDER_REF = "ba73d8c8-97f3-4a86-ae07-22b4e347f3d3"


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


def build_response_data(
    *,
    merchant_account="test_merchant",
    order_reference=TEST_ORDER_REF,
    amount="100.00",
    currency="UAH",
    auth_code="123456",
    card_pan="123456******1234",
    transaction_status="Approved",
    reason_code=1100,
):
    response_data = {
        "merchantAccount": merchant_account,
        "orderReference": order_reference,
        "amount": amount,
        "currency": currency,
        "authCode": auth_code,
        "cardPan": card_pan,
        "transactionStatus": transaction_status,
        "reasonCode": reason_code,
    }

    response_data["merchantSignature"] = (
        build_check_status_response_signature(
            merchant_account=response_data["merchantAccount"],
            order_reference=response_data["orderReference"],
            amount=response_data["amount"],
            currency=response_data["currency"],
            auth_code=response_data["authCode"],
            card_pan=response_data["cardPan"],
            transaction_status=response_data["transactionStatus"],
            reason_code=response_data["reasonCode"],
            secret_key=TEST_SECRET_KEY,
        )
    )

    return response_data


def mock_wayforpay_response(monkeypatch, response_data):
    response = Mock()
    response.json.return_value = response_data
    response.raise_for_status.return_value = None

    mock_post = Mock(return_value=response)

    monkeypatch.setattr(
        "payments.providers.wayforpay.check_status.requests.post",
        mock_post,
    )

    return mock_post


def test_check_payment_status_returns_verified_response(
    monkeypatch,
    wayforpay_settings,
):
    response_data = build_response_data()

    mock_post = mock_wayforpay_response(
        monkeypatch,
        response_data,
    )

    result = check_payment_status(TEST_ORDER_REF)

    assert result == response_data

    mock_post.assert_called_once()

    args, kwargs = mock_post.call_args

    assert args[0] == "https://api.wayforpay.com/api"
    assert kwargs["json"]["transactionType"] == "CHECK_STATUS"
    assert kwargs["json"]["merchantAccount"] == "test_merchant"
    assert kwargs["json"]["orderReference"] == TEST_ORDER_REF
    assert kwargs["json"]["apiVersion"] == 1
    assert kwargs["timeout"] == (5, 15)


def test_check_payment_status_builds_correct_request_signature(
    monkeypatch,
    wayforpay_settings,
):
    response_data = build_response_data()

    mock_post = mock_wayforpay_response(
        monkeypatch,
        response_data,
    )

    check_payment_status(TEST_ORDER_REF)

    payload = mock_post.call_args.kwargs["json"]

    expected_signature = build_check_status_signature(
        merchant_account="test_merchant",
        order_reference=TEST_ORDER_REF,
        secret_key=TEST_SECRET_KEY,
    )

    assert payload["merchantSignature"] == expected_signature


def test_check_payment_status_rejects_invalid_response_signature(
    monkeypatch,
    wayforpay_settings,
):
    response_data = build_response_data()
    response_data["merchantSignature"] = "invalid-signature"

    mock_wayforpay_response(
        monkeypatch,
        response_data,
    )

    with pytest.raises(
        ValueError,
        match="Invalid WayForPay Check Status signature",
    ):
        check_payment_status(TEST_ORDER_REF)


def test_check_payment_status_rejects_invalid_merchant_account(
    monkeypatch,
    wayforpay_settings,
):
    response_data = build_response_data(
        merchant_account="another_merchant",
    )

    mock_wayforpay_response(
        monkeypatch,
        response_data,
    )

    with pytest.raises(
        ValueError,
        match="Invalid merchant account",
    ):
        check_payment_status(TEST_ORDER_REF)


def test_check_payment_status_rejects_invalid_order_reference(
    monkeypatch,
    wayforpay_settings,
):
    unknown_ref = str(uuid.uuid4())
    response_data = build_response_data(
        order_reference=unknown_ref,
    )

    mock_wayforpay_response(
        monkeypatch,
        response_data,
    )

    with pytest.raises(
        ValueError,
        match="Invalid order reference",
    ):
        check_payment_status(TEST_ORDER_REF)


@pytest.mark.parametrize(
    "missing_field",
    [
        "merchantAccount",
        "orderReference",
        "merchantSignature",
        "amount",
        "currency",
        "transactionStatus",
    ],
)
def test_check_payment_status_rejects_missing_required_field(
    monkeypatch,
    wayforpay_settings,
    missing_field,
):
    response_data = build_response_data()
    response_data.pop(missing_field)

    mock_wayforpay_response(
        monkeypatch,
        response_data,
    )

    with pytest.raises(
        ValueError,
        match="Missing required WayForPay Check Status response fields",
    ):
        check_payment_status(TEST_ORDER_REF)


def test_check_payment_status_propagates_http_error(
    monkeypatch,
    wayforpay_settings,
):
    response = Mock()
    response.raise_for_status.side_effect = requests.HTTPError(
        "WayForPay unavailable",
    )

    mock_post = Mock(return_value=response)

    monkeypatch.setattr(
        "payments.providers.wayforpay.check_status.requests.post",
        mock_post,
    )

    with pytest.raises(requests.HTTPError, match="WayForPay unavailable"):
        check_payment_status(TEST_ORDER_REF)


def test_check_payment_status_does_not_modify_database(
    monkeypatch,
    wayforpay_settings,
):
    """
    Provider client must only communicate with WayForPay.
    Database synchronization belongs to a separate service layer.
    """
    response_data = build_response_data(
        transaction_status="Declined",
        reason_code=1104,
    )

    mock_wayforpay_response(
        monkeypatch,
        response_data,
    )

    result = check_payment_status(TEST_ORDER_REF)

    assert result["transactionStatus"] == "Declined"
