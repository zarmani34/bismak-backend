from rest_framework_nested import routers
from .views import ServiceRequestViewSet
from billings.views import QuoteViewSet

router = routers.DefaultRouter()
router.register(r'service-requests', ServiceRequestViewSet, basename='service-request')

service_request_router = routers.NestedDefaultRouter(router, r'service-requests', lookup='service_request')
service_request_router.register(r'quotes', QuoteViewSet, basename='service-request-quotes')

urlpatterns = router.urls + service_request_router.urls