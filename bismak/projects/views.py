from django.shortcuts import get_object_or_404, render
from rest_framework import viewsets
from .models import Project, ProjectAssignment, TimelineEvent
from .serializers import ProjectSerializer, ProjectAssignmentSerializer, AdminProjectSerializer, TimelineEventSerializer
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.exceptions import PermissionDenied
from commmon.permissions import IsAdminOrStaff
# from 

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