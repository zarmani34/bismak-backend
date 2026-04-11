from django.shortcuts import render

# Create your views here.

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Equipment, EquipmentCategory, EquipmentRequest, MaintenanceRequest
from .serializers import (
    EquipmentCategorySerializer,
    EquipmentListSerializer,
    EquipmentDetailSerializer,
    EquipmentRequestListSerializer,
    EquipmentRequestDetailSerializer,
    MaintenanceRequestListSerializer,
    MaintenanceRequestDetailSerializer,
)
from commmon.permissions import IsAdmin, IsAdminOrStaff


EQUIPMENT_REQUEST_TRANSITIONS = {
    'pending': ['approved', 'rejected'],
    'approved': ['returned'],
    'rejected': [],
    'returned': [],
}

MAINTENANCE_REQUEST_TRANSITIONS = {
    'pending': ['scheduled', 'rejected'],
    'scheduled': ['in_progress'],
    'in_progress': ['completed'],
    'completed': [],
}


class EquipmentCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = EquipmentCategorySerializer
    queryset = EquipmentCategory.objects.all()

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAdmin()]
        return [IsAuthenticated()]


class EquipmentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in ('admin', 'staff'):
            return Equipment.objects.all()
        raise PermissionDenied('Clients cannot access equipment.')

    def get_serializer_class(self):
        if self.action == 'list':
            return EquipmentListSerializer
        return EquipmentDetailSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAdmin()]
        return [IsAuthenticated()]

    @action(detail=True, methods=['patch'], url_path='update-status', permission_classes=[IsAdmin])
    def update_status(self, request, pk=None):
        equipment = self.get_object()
        new_status = request.data.get('status')

        valid_statuses = [s[0] for s in Equipment.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return Response(
                {'error': f'Invalid status. Valid choices are {valid_statuses}'},
                status=400
            )

        equipment.status = new_status
        equipment.save()

        return Response({
            'message': 'Equipment status updated',
            'status': new_status
        })


class EquipmentRequestViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        equipment_id = self.kwargs.get('equipment_pk')

        if equipment_id:
            equipment = get_object_or_404(Equipment, id=equipment_id)
            if user.role == 'admin':
                return EquipmentRequest.objects.filter(equipment=equipment)
            return EquipmentRequest.objects.filter(
                equipment=equipment, requested_by=user
            )

        if user.role == 'admin':
            return EquipmentRequest.objects.all()
        return EquipmentRequest.objects.filter(requested_by=user)

    def get_serializer_class(self):
        if self.action == 'list':
            return EquipmentRequestListSerializer
        return EquipmentRequestDetailSerializer

    def perform_create(self, serializer):
        if self.request.user.role not in ('staff', 'admin'):
            raise PermissionDenied('Only staff can request equipment.')

        equipment = serializer.validated_data.get('equipment')

        # check equipment is available
        if equipment.status != 'available':
            raise ValidationError(
                f'Equipment is currently {equipment.status} and cannot be requested.'
            )

        # check no pending request exists for this equipment
        if EquipmentRequest.objects.filter(
            equipment=equipment,
            status__in=['pending', 'approved']
        ).exists():
            raise ValidationError(
                'This equipment already has a pending or approved request.'
            )

        serializer.save(requested_by=self.request.user)

    @action(detail=True, methods=['patch'], url_path='update-status', permission_classes=[IsAdmin])
    def update_status(self, request, pk=None):
        equipment_request = self.get_object()
        new_status = request.data.get('status')

        if not new_status:
            return Response({'error': 'Status is required'}, status=400)

        allowed = EQUIPMENT_REQUEST_TRANSITIONS.get(equipment_request.status, [])
        if new_status not in allowed:
            return Response({
                'error': f'Cannot transition from {equipment_request.status} to {new_status}.',
                'allowed_transitions': allowed
            }, status=400)

        old_status = equipment_request.status
        equipment_request.status = new_status

        if new_status == 'approved':
            equipment_request.approved_by = request.user
            # mark equipment as in use
            equipment_request.equipment.status = 'in_use'
            equipment_request.equipment.save()

        elif new_status == 'returned':
            equipment_request.date_returned = timezone.now().date()
            # mark equipment as available again
            equipment_request.equipment.status = 'available'
            equipment_request.equipment.save()

        elif new_status == 'rejected':
            # keep equipment available
            pass

        equipment_request.save()

        return Response({
            'message': 'Equipment request status updated',
            'old_status': old_status,
            'new_status': new_status,
            'allowed_transitions': EQUIPMENT_REQUEST_TRANSITIONS.get(new_status, [])
        })


class MaintenanceRequestViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        equipment_id = self.kwargs.get('equipment_pk')

        if equipment_id:
            equipment = get_object_or_404(Equipment, id=equipment_id)
            if user.role == 'admin':
                return MaintenanceRequest.objects.filter(equipment=equipment)
            return MaintenanceRequest.objects.filter(
                equipment=equipment, requested_by=user
            )

        if user.role == 'admin':
            return MaintenanceRequest.objects.all()
        return MaintenanceRequest.objects.filter(requested_by=user)

    def get_serializer_class(self):
        if self.action == 'list':
            return MaintenanceRequestListSerializer
        return MaintenanceRequestDetailSerializer

    def perform_create(self, serializer):
        if self.request.user.role not in ('staff', 'admin'):
            raise PermissionDenied('Only staff can request maintenance.')

        serializer.save(requested_by=self.request.user)

    @action(detail=True, methods=['patch'], url_path='update-status', permission_classes=[IsAdmin])
    def update_status(self, request, pk=None):
        maintenance_request = self.get_object()
        new_status = request.data.get('status')

        if not new_status:
            return Response({'error': 'Status is required'}, status=400)

        allowed = MAINTENANCE_REQUEST_TRANSITIONS.get(maintenance_request.status, [])
        if new_status not in allowed:
            return Response({
                'error': f'Cannot transition from {maintenance_request.status} to {new_status}.',
                'allowed_transitions': allowed
            }, status=400)

        old_status = maintenance_request.status

        if new_status == 'scheduled':
            scheduled_date = request.data.get('scheduled_date')
            if not scheduled_date:
                return Response({'error': 'Scheduled date is required'}, status=400)
            maintenance_request.scheduled_date = scheduled_date
            # mark equipment under maintenance
            maintenance_request.equipment.status = 'under_maintenance'
            maintenance_request.equipment.save()

        elif new_status == 'completed':
            next_service_date = request.data.get('next_service_date')
            cost = request.data.get('cost')
            notes = request.data.get('notes', '')

            maintenance_request.completed_date = timezone.now().date()
            maintenance_request.next_service_date = next_service_date
            maintenance_request.cost = cost
            maintenance_request.notes = notes

            # update equipment
            maintenance_request.equipment.status = 'available'
            maintenance_request.equipment.last_maintenance_date = timezone.now().date()
            maintenance_request.equipment.next_maintenance_date = next_service_date
            maintenance_request.equipment.save()

        maintenance_request.status = new_status
        maintenance_request.save()

        return Response({
            'message': 'Maintenance request status updated',
            'old_status': old_status,
            'new_status': new_status,
            'allowed_transitions': MAINTENANCE_REQUEST_TRANSITIONS.get(new_status, [])
        })