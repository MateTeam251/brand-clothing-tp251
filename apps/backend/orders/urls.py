from django.urls import path

from orders.views import CustomerOrderListView, CustomerOrderDetailView

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
]

app_name = "orders"
