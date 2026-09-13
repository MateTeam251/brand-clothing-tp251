from dataclasses import dataclass

from django.conf import settings


@dataclass(frozen=True)
class WayForPayConfig:
    merchant_account: str
    secret_key: str
    merchant_domain: str
    service_url: str
    return_url: str
    api_url: str
    check_status_url: str


def get_wayforpay_config() -> WayForPayConfig:
    return WayForPayConfig(
        merchant_account=settings.WAYFORPAY_MERCHANT_ACCOUNT,
        secret_key=settings.WAYFORPAY_SECRET_KEY,
        merchant_domain=settings.WAYFORPAY_MERCHANT_DOMAIN,
        service_url=settings.WAYFORPAY_SERVICE_URL,
        return_url=settings.WAYFORPAY_RETURN_URL,
        api_url=settings.WAYFORPAY_API_URL,
        check_status_url=settings.WAYFORPAY_CHECK_STATUS_URL,
    )
