# serializers.py
from rest_framework import serializers
from dj_rest_auth.serializers import LoginSerializer as DefaultLoginSerializer, UserDetailsSerializer
from allauth.account.models import EmailAddress

class CustomLoginSerializer(DefaultLoginSerializer):
    username = None


# serializers.py

class CustomUserDetailsSerializer(UserDetailsSerializer):
    
    is_verified = serializers.SerializerMethodField()

    def get_is_verified(self, obj):
        return EmailAddress.objects.filter(user=obj, verified=True).exists()
    
    class Meta(UserDetailsSerializer.Meta):
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'role', 'date_joined', 'last_login', 'is_verified']
        read_only_fields = ('email','date_joined', 'last_login', 'is_verified', 'role')