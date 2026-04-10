from rest_framework_nested import routers
from .views import ProjectViewSet, ProjectAssignmentViewSet, TimelineEventViewSet, PressureTestViewSet, LeakTestViewSet
from billings.views import QuoteViewSet

router = routers.DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')

projects_router = routers.NestedDefaultRouter(router, r'projects', lookup='project')
projects_router.register(r'events', TimelineEventViewSet, basename='project-events')
projects_router.register(r'assignments', ProjectAssignmentViewSet, basename='assignment')
projects_router.register(r'pressure-test', PressureTestViewSet, basename='project-pressure-test')
projects_router.register(r'leak-test', LeakTestViewSet, basename='project-leak-test') 
projects_router.register(r'quotes', QuoteViewSet, basename='project-quotes')

urlpatterns = router.urls + projects_router.urls