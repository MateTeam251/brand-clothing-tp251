from django.urls import path

from orders.views import (
    CustomerOrderListView,
    CustomerOrderDetailView,
    CheckoutView
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
    # path(
    #     "checkout/",
    #     CheckoutView.as_view(),
    #     name="checkout",
    # )
]

app_name = "orders"
