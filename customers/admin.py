from django.contrib import admin

from customers.models import Customer, LoginOTP

admin.site.register(Customer)
admin.site.register(LoginOTP)
