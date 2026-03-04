from rest_framework_nested import routers
from .views import ProjectViewSet, ProjectAssignmentViewSet, TimelineEventViewSet

router = routers.DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')

projects_router = routers.NestedDefaultRouter(router, r'projects', lookup='project')
projects_router.register(r'events', TimelineEventViewSet, basename='project-events')
projects_router.register(r'assignments', ProjectAssignmentViewSet, basename='assignment')  

urlpatterns = router.urls + projects_router.urls