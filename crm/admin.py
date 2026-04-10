from django.contrib import admin
from crm.models import Lead, SaleTask, ContactActivity

admin.site.register(Lead)
admin.site.register(SaleTask)
admin.site.register(ContactActivity)
