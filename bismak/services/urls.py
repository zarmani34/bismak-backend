from rest_framework_nested import routers
from .views import ServiceRequestViewSet, ServiceTypeViewSet
from billings.views import QuoteViewSet

router = routers.DefaultRouter()
router.register(r'services', ServiceRequestViewSet, basename='service-request')
router.register(r'service-types', ServiceTypeViewSet, basename='service-type')

service_request_router = routers.NestedDefaultRouter(router, r'services', lookup='service_request')
service_request_router.register(r'quotes', QuoteViewSet, basename='service-request-quotes')

urlpatterns = router.urls + service_request_router.urls