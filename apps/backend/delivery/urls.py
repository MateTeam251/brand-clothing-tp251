from django.urls import path

from delivery.views import DeliveryCityListView, DeliveryBranchListView

urlpatterns = [
    path("cities/", DeliveryCityListView.as_view(), name="cities"),
    path("branches/", DeliveryBranchListView.as_view(), name="branches"),
]

app_name = "delivery"
