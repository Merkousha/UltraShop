from django.contrib import admin

from accounting.models import PayoutRequest, PlatformCommission, StoreTransaction

admin.site.register(StoreTransaction)
admin.site.register(PayoutRequest)
admin.site.register(PlatformCommission)
