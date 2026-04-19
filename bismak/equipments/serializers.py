from rest_framework import serializers
from .models import Equipment, EquipmentCategory, EquipmentRequest, MaintenanceRequest


class EquipmentListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Equipment
        fields = [
            'id', 'name', 'serial_number', 'model',
            'category', 'status', 'status_display',
            'next_maintenance_date'
        ]


class EquipmentDetailSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Equipment
        fields = [
            'id', 'name', 'category', 'serial_number', 'model',
            'status', 'status_display', 'description',
            'last_maintenance_date', 'next_maintenance_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'last_maintenance_date', 'created_at', 'updated_at']


class EquipmentRequestListSerializer(serializers.ModelSerializer):
    equipment_name = serializers.CharField(source='equipment.name', read_only=True)
    requested_by = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    project_code = serializers.CharField(source='project.code', read_only=True)

    class Meta:
        model = EquipmentRequest
        fields = [
            'id', 'equipment_name', 'requested_by', 'project_code',
            'status', 'status_display', 'date_needed', 'created_at'
        ]

    def get_requested_by(self, obj):
        if obj.requested_by:
            return obj.requested_by.get_full_name()
        return None


class EquipmentRequestDetailSerializer(serializers.ModelSerializer):
    equipment = EquipmentListSerializer(read_only=True)
    equipment_id = serializers.PrimaryKeyRelatedField(
        queryset=Equipment.objects.filter(status='available'),
        source='equipment',
        write_only=True
    )
    requested_by = serializers.SerializerMethodField()
    approved_by = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    project_code = serializers.CharField(source='project.code', read_only=True)

    class Meta:
        model = EquipmentRequest
        fields = [
            'id', 'equipment', 'equipment_id', 'requested_by',
            'project_code', 'status', 'status_display', 'reason',
            'approved_by', 'date_needed', 'date_returned', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'requested_by', 'approved_by', 'status',
            'date_returned', 'created_at', 'updated_at'
        ]

    def get_requested_by(self, obj):
        if obj.requested_by:
            return {
                'user_id': obj.requested_by.user_id,
                'name': obj.requested_by.get_full_name()
            }
        return None

    def get_approved_by(self, obj):
        if obj.approved_by:
            return {
                'user_id': obj.approved_by.user_id,
                'name': obj.approved_by.get_full_name()
            }
        return None


class MaintenanceRequestListSerializer(serializers.ModelSerializer):
    equipment_name = serializers.CharField(source='equipment.name', read_only=True)
    requested_by = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = MaintenanceRequest
        fields = [
            'id', 'equipment_name', 'type', 'type_display',
            'requested_by', 'status', 'status_display',
            'scheduled_date', 'created_at'
        ]

    def get_requested_by(self, obj):
        if obj.requested_by:
            return obj.requested_by.get_full_name()
        return None


class MaintenanceRequestDetailSerializer(serializers.ModelSerializer):
    equipment = EquipmentListSerializer(read_only=True)
    equipment_id = serializers.PrimaryKeyRelatedField(
        queryset=Equipment.objects.all(),
        source='equipment',
        write_only=True
    )
    requested_by = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = MaintenanceRequest
        fields = [
            'id', 'equipment', 'equipment_id', 'type', 'type_display',
            'requested_by', 'status', 'status_display', 'description',
            'scheduled_date', 'completed_date', 'next_service_date',
            'cost', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'requested_by', 'status', 'scheduled_date',
            'completed_date', 'next_service_date', 'cost',
            'notes', 'created_at', 'updated_at'
        ]

    def get_requested_by(self, obj):
        if obj.requested_by:
            return {
                'user_id': obj.requested_by.user_id,
                'name': obj.requested_by.get_full_name()
            }
        return None