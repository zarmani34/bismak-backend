from .models import Project, ProjectAssignment, TimelineEvent
from rest_framework import serializers
from accounts.serializers import UserSerializer
from accounts.models import User
from .models import PressureTest, LeakTest, LeakTestTank

# class ProjectSerializer(serializers.ModelSerializer):
#     owner = UserSerializer(read_only=True)
#     url = serializers.HyperlinkedIdentityField(view_name='project-detail', lookup_field='code')
#     class Meta:
#         model = Project
#         fields = "__all__"
#         read_only_fields = ["code", "owner", 'status', 'created_at']  # code is auto-generated, created_by is set in the view, status is read-only for non-admins


# class AdminProjectSerializer(ProjectSerializer):
#     class Meta(ProjectSerializer.Meta):
#         read_only_fields = ["code", "owner", 'created_at']  # admin can edit status

class ProjectListSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    details_url = serializers.HyperlinkedIdentityField(view_name='project-detail', lookup_field='code')

    class Meta:
        model = Project
        fields = [
            'code', 'name', 'company', 'location', 'details_url', 'type',
            'status', 'status_display', 'due_date', 'owner', 'created_at'
        ]
        read_only_fields = ['code', 'owner', 'status', 'created_at', 'type']  # code is auto-generated, owner is set in the view, status is read-only for non-admins

    def get_owner(self, obj):
        return obj.owner.get_full_name() if obj.owner else None
        
class ProjectAssignmentSerializer(serializers.ModelSerializer):
    assignee_id = serializers.SlugRelatedField(queryset=User.objects.filter(role__in=['staff', 'admin']),
        source='assignee',
        slug_field='user_id',  
        write_only=True)  
    assignee = UserSerializer(read_only=True)
    assigned_by = serializers.StringRelatedField(read_only=True)
    project = serializers.CharField(source="project.code", read_only=True)
    company = serializers.CharField(source="project.company", read_only=True)
    class Meta:
        model = ProjectAssignment
        fields = ["id", "project", "assignee", "assignment_role", "company", 'assignee_id', 'assigned_by']  # project is read-only, assignee is read-only, company is read-only
        
class TimelineEventSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    project = serializers.CharField(source="project.code", read_only=True)
    details_url = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = TimelineEvent
        fields = ['id', 'project', 'title', 'description', 'created_by', 'created_at', 'details_url']
        read_only_fields = ['id', 'created_at', 'created_by']
        
    def get_details_url(self, obj):
        return f"/api/projects/{obj.project.code}/events/{obj.id}/"
    
class PressureTestSerializer(serializers.ModelSerializer):
    project = serializers.CharField(source="project.code", read_only=True)
    result_display = serializers.CharField(source='get_result_display', read_only=True) 
    class Meta:
        model = PressureTest
        # fields = "__all__"
        fields = [
            'id', 'project',
            # Client & Location
            'client', 'location_address',
            # Equipment Details
            'manufacturer', 'manufacturing_date', 'serial_no', 'truck_no',
            'tank_capacity', 'product_stored', 'tank_type',
            # Test Details
            'test_pressure', 'working_pressure', 'temperature',
            'test_duration', 'test_medium', 'avrg_utm_gauge',
            # Safety Relief Valve
            'safety_relief_valve_size', 'safety_relief_valve_no',
            # Dates
            'date_of_test', 'next_test_date',
            # Result
            'result', 'result_display',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'project']
        
class LeakTestTankSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeakTestTank
        fields = [
            'id', 'tank_no', 'product_stored', 
            'capacity', 'age_of_tank', 'date_of_test', 'remark'
        ]
        read_only_fields = ['id']


class LeakTestSerializer(serializers.ModelSerializer):
    tanks = LeakTestTankSerializer(many=True)
    result_display = serializers.CharField(source='get_result_display', read_only=True)

    class Meta:
        model = LeakTest
        fields = [
            'id', 'project', 'station_name', 'location',
            'date_of_test', 'expiring_date', 'equipment_tested',
            'result', 'result_display', 'tanks', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        tanks_data = validated_data.pop('tanks')
        leak_test = LeakTest.objects.create(**validated_data)
        for tank_data in tanks_data:
            LeakTestTank.objects.create(leak_test=leak_test, **tank_data)
        return leak_test

    def update(self, instance, validated_data):
        tanks_data = validated_data.pop('tanks', None)
        
        # update leak test fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # if tanks are provided update them
        if tanks_data is not None:
            instance.tanks.all().delete()  # delete old tanks
            for tank_data in tanks_data:
                LeakTestTank.objects.create(leak_test=instance, **tank_data)

        return instance


class ProjectDetailSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    assignments = ProjectAssignmentSerializer(many=True, read_only=True)
    events = TimelineEventSerializer(many=True, read_only=True)
    pressure_test = PressureTestSerializer(read_only=True)
    leak_test = LeakTestSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'code', 'name', 'company', 'location',
            'status', 'status_display', 'type',
            'due_date', 'description', 'owner',
            'assignments', 'events', 'pressure_test',
            'leak_test',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'code', 'owner', 'status', 'created_at', 'updated_at', 'type']