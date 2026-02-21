from django.contrib import admin

from shipping.models import Shipment, ShippingCarrier

admin.site.register(ShippingCarrier)
admin.site.register(Shipment)
