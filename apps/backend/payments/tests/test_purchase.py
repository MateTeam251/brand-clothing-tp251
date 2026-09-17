import pytest
import requests
from django.test import override_settings

from payments.providers.wayforpay.purchase import (
    build_purchase_payload,
    send_purchase_request,
)
from payments.providers.wayforpay.signatures import build_purchase_signature


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


def test_build_purchase_payload(wayforpay_settings):
    payload = build_purchase_payload(
        order_reference="ORDER-123",
        order_date=1415379456,
        amount="2570.50",
        currency="UAH",
        product_names=[
            "Product A",
            "Product B",
        ],
        product_counts=[
            "2",
            "1",
        ],
        product_prices=[
            "1000.00",
            "570.50",
        ],
    )

    assert payload["merchantAccount"] == "test_merchant"
    assert payload["merchantDomainName"] == "www.market.ua"

    assert payload["merchantTransactionType"] == "AUTO"
    assert payload["merchantTransactionSecureType"] == "AUTO"
    assert payload["apiVersion"] == 2

    assert payload["language"] == "UA"
    assert payload["returnUrl"] == "https://market.ua/payment/success/"
    assert payload["serviceUrl"] == "https://market.ua/api/payments/wayforpay/callback/"

    assert payload["orderReference"] == "ORDER-123"
    assert payload["orderDate"] == 1415379456
    assert payload["amount"] == "2570.50"
    assert payload["currency"] == "UAH"

    assert payload["productName[]"] == [
        "Product A",
        "Product B",
    ]
    assert payload["productCount[]"] == [
        "2",
        "1",
    ]
    assert payload["productPrice[]"] == [
        "1000.00",
        "570.50",
    ]


def test_build_purchase_payload_signature(wayforpay_settings):
    payload = build_purchase_payload(
        order_reference="ORDER-123",
        order_date=1415379456,
        amount="2570.50",
        currency="UAH",
        product_names=[
            "Product A",
            "Product B",
        ],
        product_counts=[
            "2",
            "1",
        ],
        product_prices=[
            "1000.00",
            "570.50",
        ],
    )

    expected_signature = build_purchase_signature(
        merchant_account="test_merchant",
        merchant_domain="www.market.ua",
        order_reference="ORDER-123",
        order_date=1415379456,
        amount="2570.50",
        currency="UAH",
        product_names=[
            "Product A",
            "Product B",
        ],
        product_counts=[
            "2",
            "1",
        ],
        product_prices=[
            "1000.00",
            "570.50",
        ],
        secret_key=TEST_SECRET_KEY,
    )

    assert payload["merchantSignature"] == expected_signature


def test_build_purchase_payload_accepts_custom_language(wayforpay_settings):
    payload = build_purchase_payload(
        order_reference="ORDER-123",
        order_date=1415379456,
        amount="100.00",
        currency="USD",
        product_names=["Product A"],
        product_counts=["1"],
        product_prices=["100.00"],
        language="EN",
    )

    assert payload["language"] == "EN"


def test_build_purchase_payload_rejects_mismatched_product_data(wayforpay_settings):
    with pytest.raises(ValueError, match="must have the same length"):
        build_purchase_payload(
            order_reference="ORDER-123",
            order_date=1415379863,
            amount="100.00",
            currency="UAH",
            product_names=["Product A", "Product B"],
            product_counts=["1"],
            product_prices=["100.00", "50.00"],
        )


def test_send_purchase_request(monkeypatch, wayforpay_settings):
    called = {}

    def fake_post(url, data, timeout):
        called["url"] = url
        called["data"] = data
        called["timeout"] = timeout

        class FakeResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return {
                    "url": "https://wayforpay.com",
                }

        return FakeResponse()

    monkeypatch.setattr(
        "payments.providers.wayforpay.purchase.requests.post",
        fake_post,
    )

    result = send_purchase_request(
        order_reference="ORDER-123",
        order_date=1415379456,
        amount="100.00",
        currency="UAH",
        product_names=["Product A"],
        product_counts=["1"],
        product_prices=["100.00"],
    )

    assert result == "https://wayforpay.com"

    assert called["url"] == "https://secure.wayforpay.com/pay?behavior=offline"
    assert called["timeout"] == (5, 15)

    data_dict = dict(called["data"])
    assert data_dict["merchantAccount"] == "test_merchant"
    assert data_dict["orderReference"] == "ORDER-123"
    assert data_dict["amount"] == "100.00"
    assert data_dict["currency"] == "UAH"
    assert ("productName[]", "Product A") in called["data"]
    assert ("productCount[]", "1") in called["data"]
    assert ("productPrice[]", "100.00") in called["data"]


def test_send_purchase_request_raises_on_http_error(
    monkeypatch,
    wayforpay_settings,
):
    def fake_post(url, data, timeout):
        response = requests.Response()
        response.status_code = 500
        return response

    monkeypatch.setattr(
        "payments.providers.wayforpay.purchase.requests.post",
        fake_post,
    )

    with pytest.raises(requests.HTTPError):
        send_purchase_request(
            order_reference="ORDER-123",
            order_date=1415379456,
            amount="100.00",
            currency="UAH",
            product_names=["Product A"],
            product_counts=["1"],
            product_prices=["100.00"],
        )
