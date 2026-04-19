from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError

from accounts.models import User
from .models import ServiceType, ServiceRequest
from .serializers import (
    ServiceTypeSerializer,
    ServiceRequestListSerializer,
    ServiceRequestDetailSerializer
)
from commmon.permissions import IsAdminOrStaff, IsAdmin


VALID_TRANSITIONS = {
    'pending': ['reviewed', 'cancelled'],
    'reviewed': ['quoted', 'cancelled'],
    'quoted': ['accepted', 'rejected'],
    'accepted': ['in_progress'],
    'in_progress': ['completed'],
    'rejected': [],
    'completed': [],
}


class ServiceTypeViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceTypeSerializer
    permission_classes = [IsAdmin]
    queryset = ServiceType.objects.filter(is_active=True)
    pagination_class = None # disable pagination 




class ServiceRequestViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    lookup_field = 'code'  # Use code instead of id for lookups

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return ServiceRequest.objects.all()
        return ServiceRequest.objects.filter(owner=user)

    def get_serializer_class(self):
        if self.action == 'list':
            return ServiceRequestListSerializer
        return ServiceRequestDetailSerializer

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == 'client':
            serializer.save(owner=user)  # owner is themselves
        
        elif user.role in ('admin'):
            owner_id = self.request.data.get('owner')  # admin provides owner
            if not owner_id:
                raise ValidationError({'owner': 'Owner is required when creating service request as admin.'})
            
            owner = get_object_or_404(User, user_id=owner_id, role='client')  # must be a client
            serializer.save(owner=owner)

    @action(detail=True, methods=['patch'], url_path='update-status', permission_classes=[IsAdmin])
    def update_status(self, request, code=None):
        service_request = self.get_object()
        print(service_request)
        new_status = request.data.get('status')

        if not new_status:
            return Response({'error': 'Status is required'}, status=400)

        allowed = VALID_TRANSITIONS.get(service_request.status, [])
        if new_status not in allowed:
            return Response({
                'error': f'Cannot transition from {service_request.status} to {new_status}.',
                'allowed_transitions': allowed
            }, status=400)

        service_request.status = new_status
        service_request.save()

        return Response({
            'message': 'Status updated successfully',
            'old_status': service_request.status,
            'new_status': new_status,
            'allowed_transitions': VALID_TRANSITIONS.get(new_status, [])
        })
        
    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        queryset = self.get_queryset()  # respects role filtering automatically
        
        return Response({
            'total': queryset.count(),
            'pending': queryset.filter(status='pending').count(),
            'inProgress': queryset.filter(status='in_progress').count(),
            'reviewed': queryset.filter(status='reviewed').count(),
            'quoted': queryset.filter(status='quoted').count(),
            'accepted': queryset.filter(status='accepted').count(),
            'rejected': queryset.filter(status='rejected').count(),
            'completed': queryset.filter(status='completed').count(),
        })