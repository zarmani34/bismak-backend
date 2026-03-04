# serializers.py
from rest_framework import serializers
from dj_rest_auth.serializers import LoginSerializer as DefaultLoginSerializer, UserDetailsSerializer
from dj_rest_auth.registration.serializers import RegisterSerializer
from allauth.account.models import EmailAddress

from accounts.models import Organisation, User

class CustomLoginSerializer(DefaultLoginSerializer):
    username = None

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    class Meta:
        model = User
        fields = ['full_name', 'email', 'user_id', 'role']
        read_only_fields = ['email', 'full_name', 'user_id', 'role']
        


class CustomUserDetailsSerializer(UserDetailsSerializer):
    
    is_verified = serializers.SerializerMethodField()
    full_name = serializers.CharField(source='get_full_name')

    def get_is_verified(self, obj):
        return EmailAddress.objects.filter(user=obj, verified=True).exists()
    
    class Meta(UserDetailsSerializer.Meta):
        fields = ['pk', 'email', 'full_name', 'phone_number', 'role', 'date_joined', 'last_login', 'is_verified']
        read_only_fields = ('email','date_joined', 'last_login', 'is_verified', 'role', 'full_name')
        
# class CustomRegisterSerializer(RegisterSerializer):
#     username = None  # Remove username field
#     first_name = serializers.CharField(required=True)
#     last_name = serializers.CharField(required=True)

#     def get_cleaned_data(self):
#         data = super().get_cleaned_data()
#         data['first_name'] = self.validated_data.get('first_name', '')
#         data['last_name'] = self.validated_data.get('last_name', '')
#         return data

#     def save(self, request):
#         user = super().save(request)
#         user.first_name = self.cleaned_data['first_name']
#         user.last_name = self.cleaned_data['last_name']
#         user.save()
#         return user
    
    
    # Staff registration
class StaffRegisterSerializer(RegisterSerializer):
    username = None
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    employee_id = serializers.CharField(read_only=True)
    
    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data['first_name'] = self.validated_data.get('first_name', '')
        data['last_name'] = self.validated_data.get('last_name', '')
        return data

    def save(self, request):
        user = super().save(request)
        user.role = 'staff'
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()
        return user

# Admin registration
class AdminRegisterSerializer(RegisterSerializer):
    username = None
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    employee_id = serializers.CharField(read_only=True)
    
    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data['first_name'] = self.validated_data.get('first_name', '')
        data['last_name'] = self.validated_data.get('last_name', '')
        return data

    def save(self, request):
        user = super().save(request)
        user.role = 'admin'
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.is_staff = True
        user.is_superuser = True
        user.save()
        return user
    
#Client registration 
class ClientRegisterSerializer(RegisterSerializer):
    username = None 
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    company_name = serializers.CharField(required=True)
    company_address = serializers.CharField(required=False, allow_blank=True)
    
    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data['first_name'] = self.validated_data.get('first_name', '')
        data['last_name'] = self.validated_data.get('last_name', '')
        data['company_name'] = self.validated_data.get('company_name', '')
        data['company_address'] = self.validated_data.get('company_address', '')
        return data
    
    def save(self, request):
        user = super().save(request)
        user.role = 'client'
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()

        company_name = self.cleaned_data['company_name']
        company_address = self.cleaned_data['company_address']

        organisation = Organisation.objects.create(
            company_name=company_name,
            company_address=company_address
        )
        user.organisation = organisation
        user.save()
        
        return user