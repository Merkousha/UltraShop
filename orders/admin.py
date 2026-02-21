from django.contrib import admin

from orders.models import Order, OrderLine, OrderStatusEvent

admin.site.register(Order)
admin.site.register(OrderLine)
admin.site.register(OrderStatusEvent)
