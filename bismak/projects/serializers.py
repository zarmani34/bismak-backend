from .models import Project, ProjectAssignment, TimelineEvent
from rest_framework import serializers
from accounts.serializers import UserSerializer
from accounts.models import User
from .models import PressureTest

class ProjectSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name='project-detail', lookup_field='code')
    class Meta:
        model = Project
        fields = "__all__"
        read_only_fields = ["code", "owner", 'status', 'created_at']  # code is auto-generated, created_by is set in the view, status is read-only for non-admins
    

class AdminProjectSerializer(ProjectSerializer):
    class Meta(ProjectSerializer.Meta):
        read_only_fields = ["code", "owner", 'created_at']  # admin can edit status
        
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