# apps/services/serializers.py
from rest_framework import serializers
from .models import ServiceType, ServiceRequest


class ServiceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceType
        fields = ['id', 'name', 'description', 'is_active']
        read_only_fields = ['id']


class ServiceRequestListSerializer(serializers.ModelSerializer):
    service_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)

    class Meta:
        model = ServiceRequest
        fields = [
            'id', 'name', 'service_name', 'location',
            'status', 'status_display', 'owner_name', 'created_at'
        ]

    def get_service_name(self, obj):
        return obj.get_service_name()


class ServiceRequestDetailSerializer(serializers.ModelSerializer):
    service_name = serializers.SerializerMethodField()
    service_type = ServiceTypeSerializer(read_only=True)
    service_type_id = serializers.PrimaryKeyRelatedField(
        queryset=ServiceType.objects.filter(is_active=True),
        source='service_type',
        write_only=True,
        required=False,
        allow_null=True
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    owner = serializers.SerializerMethodField()

    class Meta:
        model = ServiceRequest
        fields = [
            'id', 'name', 'service_type', 'service_type_id',
            'custom_service', 'service_name', 'location',
            'description', 'status', 'status_display',
            'owner', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'owner', 'created_at', 'updated_at']

    def get_service_name(self, obj):
        return obj.get_service_name()

    def get_owner(self, obj):
        return {
            'user_id': obj.owner.user_id,
            'name': obj.owner.get_full_name(),
        }

    def validate(self, data):
        if not data.get('service_type') and not data.get('custom_service'):
            raise serializers.ValidationError(
                'Either service type or custom service must be provided.'
            )
        return data