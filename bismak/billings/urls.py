from rest_framework_nested import routers
from .views import QuoteViewSet, InvoiceViewSet

router = routers.DefaultRouter()
router.register(r'quotes', QuoteViewSet, basename='quote')

quotes_router = routers.NestedDefaultRouter(router, r'quotes', lookup='quote')
quotes_router.register(r'invoice', InvoiceViewSet, basename='quote-invoice')

urlpatterns = router.urls + quotes_router.urls