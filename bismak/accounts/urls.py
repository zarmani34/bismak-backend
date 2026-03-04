from django.urls import path, include
from rest_framework_nested import routers
from accounts.views import ClientRegisterView, StaffRegisterView, AdminRegisterView, UserViewSet

router = routers.DefaultRouter()
router.register(r'users', UserViewSet, basename='users')


urlpatterns = [
    path('auth/', include(router.urls)),
    path('auth/registration/staff/', StaffRegisterView.as_view(), name='staff-register'),
    path('auth/registration/admin/', AdminRegisterView.as_view(), name='admin-register'),
    path('auth/registration/client/', ClientRegisterView.as_view(), name='client-register'),
]