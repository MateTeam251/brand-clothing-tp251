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
        "<int:pk>/",
        CustomerOrderDetailView.as_view(),
        name="order-detail",
    ),
    path(
        "checkout/",
        CheckoutView.as_view(),
        name="checkout",
    ),
    path(
        "<int:pk>/retry-payment/",
        RetryPaymentView.as_view(),
        name="retry-payment",
    )
]

app_name = "orders"
