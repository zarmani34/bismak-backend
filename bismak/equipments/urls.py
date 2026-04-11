from rest_framework_nested import routers
from .views import (
    EquipmentCategoryViewSet,
    EquipmentViewSet,
    EquipmentRequestViewSet,
    MaintenanceRequestViewSet
)

router = routers.DefaultRouter()
router.register(r'equipment-categories', EquipmentCategoryViewSet, basename='equipment-category')
router.register(r'equipment', EquipmentViewSet, basename='equipment')
router.register(r'equipment-requests', EquipmentRequestViewSet, basename='equipment-request')
router.register(r'maintenance-requests', MaintenanceRequestViewSet, basename='maintenance-request')

# nested under equipment
equipment_router = routers.NestedDefaultRouter(router, r'equipment', lookup='equipment')
equipment_router.register(r'requests', EquipmentRequestViewSet, basename='equipment-requests')
equipment_router.register(r'maintenance', MaintenanceRequestViewSet, basename='equipment-maintenance')

urlpatterns = router.urls + equipment_router.urls