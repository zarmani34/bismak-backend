from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from .models import PressureTest, Project, ProjectAssignment, TimelineEvent, ProjectStatus
from .serializers import ProjectAssignmentSerializer, TimelineEventSerializer, ProjectDetailSerializer, ProjectListSerializer, PressureTestSerializer, LeakTestSerializer
from rest_framework.exceptions import PermissionDenied, ValidationError
from commmon.permissions import IsAdminOrStaff
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
# Create your views here.

class ProjectViewSet(viewsets.ModelViewSet):
    # filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    # filterset_fields = ['status', 'location', 'client']
    # search_fields = ['name', 'owner__first_name']
    lookup_field = 'code'  # Use code instead of id for lookups
    
    def get_queryset(self):
        user = self.request.user
        if user.role in ('staff', 'admin'):
            return Project.objects.all()
        return Project.objects.filter(owner=user)  # clients only see their own projects
    
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
        
    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectListSerializer
        return ProjectDetailSerializer
    
    @action(detail=True, methods=['patch'], url_path='update-status', permission_classes=[IsAdminOrStaff])
    def update_status(self, request, **kwargs):
        project = self.get_object()
        new_status = request.data.get('status')
        VALID_TRANSITIONS = {
        'planning':    ['in_progress', 'cancelled'],
        'in_progress': ['on_hold', 'completed', 'cancelled'],
        'on_hold':     ['in_progress', 'cancelled'],
        'completed':   [],
        'cancelled':   [],
        }

        # check status was provided
        if not new_status:
            return Response(
                {'error': 'Status is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_status not in ProjectStatus.values:
            return Response(
                {'error': f'Invalid status. Valid choices are {ProjectStatus.values}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        allowed_transitions = VALID_TRANSITIONS.get(project.status, [])
        if new_status not in allowed_transitions:
            return Response(
                {
                    'error': f'Cannot transition from {project.status} to {new_status}.',
                    'allowed_transitions': allowed_transitions
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        old_status = project.status
        project.status = new_status
        project.save()

        TimelineEvent.objects.create(
            project=project,
            title="Status Updated",
            description=f"Status changed from {old_status} to {new_status}",
            created_by=request.user
        )

        return Response({
            'message': 'Status updated successfully',
            'old_status': old_status,
            'new_status': new_status,
            'allowed_transitions': VALID_TRANSITIONS.get(new_status, [])
        })

class ProjectAssignmentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrStaff]
    serializer_class = ProjectAssignmentSerializer
    # queryset = ProjectAssignment.objects.all()
    
    def get_queryset(self):
        project_code = self.kwargs.get('project_code')
        project = get_object_or_404(Project, code=project_code)
        
        return ProjectAssignment.objects.filter(project=project)
    
    def perform_create(self, serializer):
        project_code = self.kwargs.get('project_code')
        project = Project.objects.filter(code=project_code).first()
        
        if not project:
            raise PermissionDenied("Project not found.")
        
        TimelineEvent.objects.create(
            project=project,
            title="Project Assigned",
            description=f"Project assigned to {serializer.validated_data['assignee'].get_full_name()}, role is: {serializer.validated_data.get('assignment_role', 'N/A')}",
            created_by=self.request.user
        )
        
        serializer.save(project=project, assigned_by=self.request.user)

class TimelineEventViewSet(viewsets.ModelViewSet):
    serializer_class = TimelineEventSerializer
    permission_classes = [IsAdminOrStaff]
    
    def get_queryset(self):
        project_code = self.kwargs.get('project_code')
        project = get_object_or_404(Project, code=project_code)
        
        user = self.request.user        
        if user.role == 'client':
            if project.owner != user:
                raise PermissionDenied("You do not have access to this project.")

        return TimelineEvent.objects.filter(project=project).order_by('created_at')
    
    def perform_create(self, serializer):
        
        project_code = self.kwargs.get('project_code')
        project = get_object_or_404(Project, code=project_code)
        
        serializer.save(created_by=self.request.user, project=project)

class BaseProjectTypeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrStaff]
    project_type = None

    def get_queryset(self):
        project_code = self.kwargs.get('project_code')
        project = get_object_or_404(Project, code=project_code)
        
        return self.queryset.filter(project=project)
        
    def perform_create(self, serializer):
        
        project_code = self.kwargs.get('project_code')
        project = get_object_or_404(Project, code=project_code)

        if project.type is not None:
            raise ValidationError(f'Project already has a {project.type} record.')

        project.type = self.project_type
        project.status = 'in_progress'
        project.save()
        
        TimelineEvent.objects.create(
            project=project,
            title="Project Executed",
            description=f"Project executed as: {self.project_type}, by {self.request.user.get_full_name()}",
            created_by=self.request.user
        )
        
        serializer.save(project=project)
        
    def perform_destroy(self, instance):
        project = instance.project
        instance.delete()
        project.type = None
        project.save()
   
class PressureTestViewSet(BaseProjectTypeViewSet):
    project_type = 'pressure_test'
    serializer_class = PressureTestSerializer
    queryset = PressureTest.objects.all()


class LeakTestViewSet(BaseProjectTypeViewSet):
    project_type = 'leak_test'
    serializer_class = LeakTestSerializer
    queryset = PressureTest.objects.all()
        
# Project will be in two views 
# for users like staff to request project and for admin or staff to update
        
        
# On assigning a project to a user, we should update the project status to in progress
# Upon executing projects e.e leaktest, calibration etc, 
# on save project.status should be updated to completed and when the test is completed, it should be updated to completed. 
# This can be done by overriding the save method of the respective test models and updating the project status accordingly.
# we need a logic to update project status to completed, on hold or cancelled as well, this can be done by creating a separate endpoint for updating project status and allowing only admin to update it.