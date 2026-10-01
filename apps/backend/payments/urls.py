from django.urls import path

from payments.views import WayForPayCallbackView, PaymentSuccessView

urlpatterns = [
    path(
        "wayforpay/callback/",
        WayForPayCallbackView.as_view(),
        name="wayforpay-callback"
    ),
    path(
        "success/",
        PaymentSuccessView.as_view(),
        name="payment-success"
    )
]

app_name = "payments"
