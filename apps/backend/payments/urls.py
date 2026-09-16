from django.urls import path

from payments.views import WayForPayCallbackView

urlpatterns = [
    path(
        "wayforpay/callback/",
        WayForPayCallbackView.as_view(),
        name="wayforpay-callback"
    )
]

app_name = "payments"
