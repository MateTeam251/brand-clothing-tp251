from django.urls import path

from payments.views import WayForPayCallbackView, PaymentReturnView

urlpatterns = [
    path(
        "wayforpay/callback/",
        WayForPayCallbackView.as_view(),
        name="wayforpay-callback"
    ),
    path(
        "wayforpay/return/",
        PaymentReturnView.as_view(),
        name="wayforpay-return"
    )
]

app_name = "payments"
