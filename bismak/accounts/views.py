from django.shortcuts import render

# Create your views here.
from dj_rest_auth.registration.views import RegisterView
from rest_framework.permissions import IsAdminUser

from .models import User
from .serializers import  ClientRegisterSerializer, StaffRegisterSerializer, AdminRegisterSerializer, UserSerializer
from rest_framework import viewsets

class StaffRegisterView(RegisterView):
    serializer_class = StaffRegisterSerializer
    permission_classes = [IsAdminUser]

class AdminRegisterView(RegisterView):
    serializer_class = AdminRegisterSerializer
    permission_classes = [IsAdminUser]
    
class ClientRegisterView(RegisterView):
    serializer_class = ClientRegisterSerializer
    
class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'user_id'
    
    def get_queryset(self):
        if self.request.user.role == 'client':
            return User.objects.filter(id=self.request.user.id) # for now use id and change to user_id later
        return User.objects.all()
            


# class ClientUserViewSet(viewsets.ModelViewSet):
#     serializer_class = AdminStaffSerializer  # You can create a separate serializer for clients if needed
#     permission_classes = [IsAdminUser]
    
#     def get_queryset(self):
#         return User.objects.filter(role='client')

# class OrganisationViewSet(viewsets.ModelViewSet):
#     serializer_class = OrganisationSerializer

#     def get_queryset(self):
#         user = self.request.user
#         # admin and staff can see all organisations
#         if user.role in ('admin', 'staff'):
#             return Organisation.objects.all()
#         # client can only see their own organisation
#         if user.role == 'client' and user.organisation:
#             return Organisation.objects.filter(id=user.organisation.id)
#         return Organisation.objects.none()

#     def perform_create(self, serializer):
#         # only admin and staff can create organisations manually
#         if self.request.user.role not in ('admin', 'staff'):
#             raise PermissionDenied("You do not have permission to create an organisation.")
#         serializer.save()

#     def perform_update(self, serializer):
#         user = self.request.user
#         # admin can update any organisation
#         # client can only update their own
#         if user.role == 'client' and serializer.instance != user.organisation:
#             raise PermissionDenied("You can only update your own organisation.")
#         serializer.save()

#     def perform_destroy(self, instance):
#         # only admin can delete organisations
#         if self.request.user.role != 'admin':
#             raise PermissionDenied("Only admins can delete organisations.")
#         instance.delete()


# class UserViewSet(viewsets.ModelViewSet):

#     def get_queryset(self):
#         user = self.request.user
#         if user.role in ('admin', 'staff'):
#             return User.objects.all()
#         # client can only see their own profile
#         return User.objects.filter(id=user.id)

#     def get_serializer_class(self):
#         # check the role of the user being created or the current user
#         if self.action == 'create':
#             role = self.request.data.get('role')
#         else:
#             role = self.request.user.role

#         if role == 'client':
#             return ClientUserSerializer
#         return UserSerializer

#     def perform_create(self, serializer):
#         role = self.request.data.get('role')
#         if role == 'client':
#             company_name = self.request.data.get('company_name')
#             company_address = self.request.data.get('company_address', '')

#             organisation = Organisation.objects.create(
#                 company_name=company_name,
#                 company_address=company_address
#             )
#             serializer.save(organisation=organisation)
#         else:
#             serializer.save()