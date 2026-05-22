from django.contrib import admin
from .models import EquipmentCategory, Equipment, EquipmentRequest, MaintenanceRequest

# Register your models here.
admin.site.register(EquipmentCategory)
admin.site.register(Equipment)
admin.site.register(EquipmentRequest)
admin.site.register(MaintenanceRequest)