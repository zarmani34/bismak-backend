from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from .models import Project, ProjectAssignment, TimelineEvent, ProjectStatus
from .serializers import ProjectSerializer, ProjectAssignmentSerializer, AdminProjectSerializer, TimelineEventSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from commmon.permissions import IsAdminOrStaff
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
# Create your views here.

class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
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
              
        if self.request.user.role == "admin":
            return AdminProjectSerializer  # admin gets full access
        return ProjectSerializer
    
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
        project = Project.objects.filter(code=project_code).first()
        
        if not project:
            raise PermissionDenied("Project not found.")
        
        serializer.save(created_by=self.request.user, project=project)

class BaseProjectTypeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrStaff]
    project_type = None

    def perform_create(self, serializer):
        project_code = self.kwargs.get('project_pk')
        project = Project.objects.filter(code=project_code).first()

        project.type = self.project_type
        project.save()
        serializer.save(project=project)
        
        
        # Project will be in two views 
        # for users like staf to request project and for admin or staff to update
        
        
# On assigning a project to a user, we should update the project status to in progress
# Upon executing projects e.e leaktest, calibration etc, 
# on save project.status should be updated to completed and when the test is completed, it should be updated to completed. 
# This can be done by overriding the save method of the respective test models and updating the project status accordingly.
# we need a logic to update project status to completed, on hold or cancelled as well, this can be done by creating a separate endpoint for updating project status and allowing only admin to update it.