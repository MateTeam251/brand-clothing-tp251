from payments.providers.wayforpay.signatures import (
    build_callback_response_signature,
    build_callback_signature,
    build_check_status_response_signature,
    build_check_status_signature,
    build_purchase_signature,
    verify_signature,
    _build_signature,
)


TEST_SECRET_KEY = "dhkq3vUi94{Z!5frxs(02ML"


def test_build_signature():
    signature = _build_signature(
        "merchant",
        "order-123",
        "100.00",
        secret_key="secret"
    )

    assert signature == "33359fd577eb432921a64108701df323"


def test_build_signature_with_none_values():
    signature_with_none = _build_signature(
        "merchant",
        "order-123",
        "100.00",
        None,
        "44****1212",
        None,
        secret_key="secret",
    )

    signature_with_empty_strings = _build_signature(
        "merchant",
        "order-123",
        "100.00",
        "",
        "44****1212",
        "",
        secret_key="secret",
    )

    assert signature_with_none == signature_with_empty_strings
    assert signature_with_none == "c45da2dfc64c179dd497a479a518e762"


def test_build_callback_signature_with_none():
    signature = build_callback_signature(
        merchant_account="test_merch_n1",
        order_reference="DH783023",
        amount="100",
        currency="UAH",
        auth_code=None,
        card_pan="44****1212",
        transaction_status="Declined",
        reason_code=None,
        secret_key=TEST_SECRET_KEY,
    )

    assert signature == "dd7f577f41aa591e0a38c0c1367af07a"


def test_build_purchase_signature():
    signature = build_purchase_signature(
        merchant_account="test_merch_n1",
        merchant_domain="www.market.ua",
        order_reference="DH783023",
        order_date=1415379863,
        amount="1547.36",
        currency="UAH",
        product_names=[
            "Процесор Intel Core i5-4670 3.4GHz",
            "Пам'ять Kingston DDR3-1600 4096MB PC3-12800",
        ],
        product_counts=["1", "1"],
        product_prices=["1000", "547.36"],
        secret_key=TEST_SECRET_KEY,
    )

    # WayForPay documentation publishes b95932786cbe243a76b014846b63fe92
    # for this example. However, that value does not match the HMAC-MD5
    # calculation for the published input data.
    assert signature == "a2ff08c4a1818b8f0e719cfce5813935"


def test_build_callback_signature():
    signature = build_callback_signature(
        merchant_account="test_merch_n1",
        order_reference="DH783023",
        amount="100",
        currency="UAH",
        auth_code="221562",
        card_pan="44****1212",
        transaction_status="Approved",
        reason_code="1100",
        secret_key=TEST_SECRET_KEY,
    )

    assert signature == "ec57553c8db1ac883ec2ea268e5b0ebc"


def test_build_callback_response_signature():
    signature = build_callback_response_signature(
        order_reference="DH783023",
        status="accept",
        timestamp=1415379863,
        secret_key=TEST_SECRET_KEY
    )

    assert signature == "1961b1e9819c7f651a85b7d88b8859ef"


def test_build_check_status_signature():
    signature = build_check_status_signature(
        merchant_account="test_merch_n1",
        order_reference="DH783023",
        secret_key=TEST_SECRET_KEY,
    )

    assert signature == "cfa91a1121e0138f25fc01af28dcaf2b"


def test_build_check_status_response_signature():
    signature = build_check_status_response_signature(
        merchant_account="test_merch_n1",
        order_reference="DH783023",
        amount="100",
        currency="UAH",
        auth_code="221562",
        card_pan="44****1212",
        transaction_status="Approved",
        reason_code="1100",
        secret_key=TEST_SECRET_KEY,
    )

    assert signature == "ec57553c8db1ac883ec2ea268e5b0ebc"


def test_verify_signature():
    assert verify_signature(
        received_signature="abc123",
        expected_signature="abc123",
    )

    assert not verify_signature(
        received_signature="abc123",
        expected_signature="different",
    )
