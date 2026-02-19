# serializers.py
from rest_framework import serializers
from dj_rest_auth.serializers import LoginSerializer as DefaultLoginSerializer, UserDetailsSerializer
from dj_rest_auth.registration.serializers import RegisterSerializer
from allauth.account.models import EmailAddress

class CustomLoginSerializer(DefaultLoginSerializer):
    username = None



class CustomUserDetailsSerializer(UserDetailsSerializer):
    
    is_verified = serializers.SerializerMethodField()

    def get_is_verified(self, obj):
        return EmailAddress.objects.filter(user=obj, verified=True).exists()
    
    class Meta(UserDetailsSerializer.Meta):
        fields = ['pk', 'email', 'first_name', 'last_name', 'phone_number', 'role', 'date_joined', 'last_login', 'is_verified']
        read_only_fields = ('email','date_joined', 'last_login', 'is_verified', 'role')
        
class CustomRegisterSerializer(RegisterSerializer):
    username = None  # Remove username field
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data['first_name'] = self.validated_data.get('first_name', '')
        data['last_name'] = self.validated_data.get('last_name', '')
        return data

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()
        return user
    
    
    # Staff registration
class StaffRegisterSerializer(RegisterSerializer):
    username = None
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    
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