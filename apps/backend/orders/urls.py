from django.urls import path

from orders.views import (
    CustomerOrderListView,
    CustomerOrderDetailView,
    CheckoutView,
    RetryPaymentView,
    OrderStatusView,
    CheckoutFopView,
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
      "checkout-fop/",
        CheckoutFopView.as_view(),
        name="checkout-fop",
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
    ),
    path(
        "<str:order_reference>/status/",
        OrderStatusView.as_view(),
        name="order-status",
    )
]

app_name = "orders"
