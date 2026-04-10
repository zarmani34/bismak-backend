from django.contrib import admin
from .models import ServiceType, ServiceRequest

# Register your models here.
admin.site.register(ServiceType)
admin.site.register(ServiceRequest)