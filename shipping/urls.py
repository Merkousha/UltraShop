from django.urls import path
from . import views

app_name = "shipping"

urlpatterns = [
    path("dashboard/orders/<int:order_id>/create-shipment/", views.CreateShipmentView.as_view(), name="create_shipment"),
    path("track/<int:shipment_id>/", views.TrackShipmentView.as_view(), name="track"),
]
