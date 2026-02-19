from django.shortcuts import render

# Create your views here.
from dj_rest_auth.registration.views import RegisterView
from rest_framework.permissions import IsAdminUser
from .serializers import  StaffRegisterSerializer, AdminRegisterSerializer

class StaffRegisterView(RegisterView):
    serializer_class = StaffRegisterSerializer
    permission_classes = [IsAdminUser]

class AdminRegisterView(RegisterView):
    serializer_class = AdminRegisterSerializer
    permission_classes = [IsAdminUser]