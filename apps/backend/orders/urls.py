from django.urls import path

from orders.views import (
    CustomerOrderListView,
    CustomerOrderDetailView,
    CheckoutView,
    RetryPaymentView,
)

urlpatterns = [
    path(
        "",
        CustomerOrderListView.as_view(),
        name="order-list",
    ),
    path(
        "checkout/",
        CheckoutView.as_view(),
        name="checkout",
    ),
    path(
        "<str:order_reference>/",
        CustomerOrderDetailView.as_view(),
        name="order-detail",
    ),
    path(
        "<str:order_reference>/retry-payment/",
        RetryPaymentView.as_view(),
        name="retry-payment",
    )
]

app_name = "orders"
