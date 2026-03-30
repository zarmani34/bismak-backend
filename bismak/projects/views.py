from django.shortcuts import get_object_or_404
from rest_framework import viewsets

from accounts.models import User
from .models import PressureTest, Project, ProjectAssignment, ProjectTypes, TimelineEvent, ProjectStatus, LeakTest
from .serializers import ProjectAssignmentSerializer, TimelineEventSerializer, ProjectDetailSerializer, ProjectListSerializer, PressureTestSerializer, LeakTestSerializer
from rest_framework.exceptions import PermissionDenied, ValidationError
from commmon.permissions import IsAdminOrStaff, IsAdmin
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
# Create your views here.

class ProjectViewSet(viewsets.ModelViewSet):
    # filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    # filterset_fields = ['status', 'location', 'client']
    # search_fields = ['name', 'owner__first_name']
    lookup_field = 'code'  # Use code instead of id for lookups
    
    def get_project(self):
        project_code = self.kwargs.get('project_code')
        return get_object_or_404(Project, code=project_code)
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Project.objects.all()
        elif user.role == 'staff':
            return Project.objects.filter(assignments__assignee=user)
        return Project.objects.filter(owner=user)  # client  # clients only see their own projects
    
    
    def perform_create(self, serializer):
        user = self.request.user
    
        if user.role == 'client':
            serializer.save(owner=user)  # owner is themselves
            
        elif user.role in ('admin', 'staff'):
            owner_id = self.request.data.get('owner')  # admin provides owner
            if not owner_id:
                raise ValidationError({'owner': 'Owner is required when creating project as admin.'})
            
            owner = get_object_or_404(User, user_id=owner_id, role='client')  # must be a client
            serializer.save(owner=owner)
        
    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectListSerializer
        return ProjectDetailSerializer
    
    @action(detail=True, methods=['patch'], url_path='update-status', permission_classes=[IsAdmin])
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

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        queryset = self.get_queryset()  # respects role filtering automatically
        
        return Response({
            'total': queryset.count(),
            'planning': queryset.filter(status='planning').count(),
            'in_progress': queryset.filter(status='in_progress').count(),
            'on_hold': queryset.filter(status='on_hold').count(),
            'completed': queryset.filter(status='completed').count(),
            'cancelled': queryset.filter(status='cancelled').count(),
        })
        
    # def admin_user

class ProjectAssignmentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrStaff]
    serializer_class = ProjectAssignmentSerializer
    # queryset = ProjectAssignment.objects.all()
    
    def get_project(self):
        project_code = self.kwargs.get('project_code')
        return get_object_or_404(Project, code=project_code)
    
    def get_queryset(self):
        project = self.get_project()
        
        return ProjectAssignment.objects.filter(project=project)
    
    def perform_create(self, serializer):
        project = self.get_project()
        if project.status == ProjectStatus.PLANNING:
            project.status = ProjectStatus.IN_PROGRESS
            project.save()
               
        serializer.save(project=project, assigned_by=self.request.user)
        
        TimelineEvent.objects.create(
            project=project,
            title="Project Assigned and status updated",
            description=f"Project assigned to {serializer.validated_data['assignee'].get_full_name()}, role is: {serializer.validated_data.get('assignment_role', 'N/A')}",
            created_by=self.request.user
        )
        
    def perform_destroy(self, instance):
        project = instance.project
        assignee_name = instance.assignee.get_full_name()
        
        instance.delete()
        
        TimelineEvent.objects.create(
            project=project,
            title="Project Unassigned",
            description=f"Project unassigned from {assignee_name}, role was: {instance.assignment_role}",
            created_by=self.request.user
        )
class TimelineEventViewSet(viewsets.ModelViewSet):
    serializer_class = TimelineEventSerializer
    permission_classes = [IsAdminOrStaff]
    
    def get_project(self):
        project_code = self.kwargs.get('project_code')
        return get_object_or_404(Project, code=project_code)
    
    def get_queryset(self):
        project = self.get_project()
        
        user = self.request.user        
        if user.role == 'client':
            if project.owner != user:
                raise PermissionDenied("You do not have access to this project.")

        return TimelineEvent.objects.filter(project=project).order_by('created_at')
    
    def perform_create(self, serializer):
        project = self.get_project()
        
        serializer.save(created_by=self.request.user, project=project)

class BaseProjectTypeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrStaff]
    
    def get_project(self):
        project_code = self.kwargs.get('project_code')
        return get_object_or_404(Project, code=project_code)

    def get_queryset(self):
        project = self.get_project()
        return self.queryset.filter(project=project)
        
    def perform_create(self, serializer):
        project = self.get_project()

        if project.type != self.project_type:
            raise ValidationError(
                f'This project is a {project.type} project not {self.project_type}.'
            )
            
        if self.queryset.filter(project=project).exists():
            raise ValidationError(
                f'This project already has a {self.project_type} record.'
            )

        TimelineEvent.objects.create(
            project=project,
            title="Project Executed",
            description=f"Project executed as {project.type} by {self.request.user.get_full_name()}",
            created_by=self.request.user
        )
        
        serializer.save(project=project)
        
    
   
class PressureTestViewSet(BaseProjectTypeViewSet):
    project_type = ProjectTypes.PRESSURE_TEST
    serializer_class = PressureTestSerializer
    queryset = PressureTest.objects.all()


class LeakTestViewSet(BaseProjectTypeViewSet):
    project_type = ProjectTypes.LEAK_TEST
    serializer_class = LeakTestSerializer
    queryset = LeakTest.objects.all()
        
# Project will be in two views 
# for users like staff to request project and for admin or staff to update
        
        
# On assigning a project to a user, we should update the project status to in progress
# Upon executing projects e.e leaktest, calibration etc, 
# on save project.status should be updated to completed and when the test is completed, it should be updated to completed. 
# This can be done by overriding the save method of the respective test models and updating the project status accordingly.
# we need a logic to update project status to completed, on hold or cancelled as well, this can be done by creating a separate endpoint for updating project status and allowing only admin to update it.