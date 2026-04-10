from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Quote, Invoice
from .serializers import QuoteListSerializer, QuoteDetailSerializer, InvoiceSerializer
from commmon.permissions import IsAdmin
from services.models import ServiceRequest
from projects.models import Project


QUOTE_VALID_TRANSITIONS = {
    'draft': ['sent'],
    'sent': ['accepted', 'rejected', 'revised'],
    'revised': ['sent'],
    'accepted': [],
    'rejected': [],
}


class QuoteViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    lookup_field = 'code'  # Use code instead of id for lookups
    
    # This method will be used to determine if project or services is in the nested url
    def get_project(self):
        project_code = self.kwargs.get('project_code')
    
        if project_code:
            return get_object_or_404(Project, code=project_code)
        return None
        
    def get_service_request(self):
        service_request_code = self.kwargs.get('service_request_code')
    
        if service_request_code:
            return get_object_or_404(ServiceRequest, code=service_request_code)
        return None 

    def get_queryset(self):
        user = self.request.user
        project = self.get_project()
        service_request = self.get_service_request()

        if project:
            # role check for project quotes
            if user.role == 'admin':
                return Quote.objects.filter(project=project)
            elif user.role == 'staff':
                # staff can only see quotes for projects they are assigned to
                if not project.assignments.filter(assignee=user).exists():
                    raise PermissionDenied('You do not have access to this project.')
                return Quote.objects.filter(project=project)
            else:
                # client can only see quotes for their own projects
                if project.owner != user:
                    raise PermissionDenied('You do not have access to this project.')
                return Quote.objects.filter(project=project)

        if service_request:
            # role check for service request quotes
            if user.role == 'admin':
                return Quote.objects.filter(service_request=service_request)
            elif user.role == 'staff':
                raise PermissionDenied('Staff cannot access service request quotes.')
            else:
                # client can only see quotes for their own service requests
                if service_request.owner != user:
                    raise PermissionDenied('You do not have access to this service request.')
                return Quote.objects.filter(service_request=service_request)

         # standalone /quotes/ endpoint
        if user.role == 'admin':
            return Quote.objects.all()
        elif user.role == 'client':
            # client sees all quotes linked to them
            return Quote.objects.filter(
                service_request__owner=user
            ) | Quote.objects.filter(
                project__owner=user
            )
        # staff has no standalone quotes access
        raise PermissionDenied('Staff can only access quotes through a project.') 

    def get_serializer_class(self):
        if self.action == 'list':
            return QuoteListSerializer
        return QuoteDetailSerializer

    def perform_create(self, serializer):
        project = self.get_project()
        service_request = self.get_service_request()
        
        if self.request.user.role not in ('admin'):
            raise PermissionDenied('Only admin can create quotes.')
        
        if project and service_request:
            raise ValidationError('Quote can only be linked to either a project or a service request, not both.')
        if not project and not service_request:
            raise ValidationError('Quote must be linked to either a project or a service request.')

         # enforce one quote per project
        if project and Quote.objects.filter(project=project).exists():
            raise ValidationError(f'Project {project.code} already has a quote.')

        # enforce one quote per service request
        if service_request and Quote.objects.filter(service_request=service_request).exists():
            raise ValidationError(f'This service request already has a quote.')
        
        if project :
            serializer.save(quoted_by=self.request.user, project=project)
        else:
            serializer.save(quoted_by=self.request.user, service_request=service_request)

    @action(detail=True, methods=['patch'], url_path='update-status')
    def update_status(self, request, pk=None):
        quote = self.get_object()
        new_status = request.data.get('status')

        if not new_status:
            return Response({'error': 'Status is required'}, status=400)

        allowed = QUOTE_VALID_TRANSITIONS.get(quote.status, [])
        if new_status not in allowed:
            return Response({
                'error': f'Cannot transition from {quote.status} to {new_status}.',
                'allowed_transitions': allowed
            }, status=400)

        old_status = quote.status
        quote.status = new_status

        # set timestamps
        if new_status == 'accepted':
            quote.accepted_at = timezone.now()
            # auto create invoice when quote accepted
            Invoice.objects.create(
                quote=quote,
                amount=quote.amount,
                due_date=quote.valid_until
            )
            # update service request status if linked
            if quote.service_request:
                quote.service_request.status = 'accepted'
                quote.service_request.save()

        elif new_status == 'rejected':
            quote.rejected_at = timezone.now()
            if quote.service_request:
                quote.service_request.status = 'rejected'
                quote.service_request.save()

        quote.save()

        return Response({
            'message': 'Quote status updated',
            'old_status': old_status,
            'new_status': new_status,
            'allowed_transitions': QUOTE_VALID_TRANSITIONS.get(new_status, [])
        })


class InvoiceViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        quote_code = self.kwargs.get('quote_code')

        if quote_code:
            quote = get_object_or_404(Quote, code=quote_code)
            # check access to parent quote
            if user.role == 'admin':
                return Invoice.objects.filter(quote=quote)
            elif user.role == 'client':
                has_access = (
                    quote.project and quote.project.owner == user or
                    quote.service_request and quote.service_request.owner == user
                )
                if not has_access:
                    raise PermissionDenied('You do not have access to this invoice.')
                return Invoice.objects.filter(quote=quote)
            raise PermissionDenied('Staff cannot access invoices through quotes.')

        # standalone /invoices/ endpoint
        if user.role == 'admin':
            return Invoice.objects.all()
        elif user.role == 'client':
            # client sees all invoices linked to them
            return Invoice.objects.filter(
                quote__service_request__owner=user
            ) | Invoice.objects.filter(
                quote__project__owner=user
            )
        raise PermissionDenied('Staff can only access invoices through a project.')

    def get_serializer_class(self):
        return InvoiceSerializer

    def perform_create(self, serializer):
        if self.request.user.role not in ('admin',):
            raise PermissionDenied('Only admin can create invoices.')
        serializer.save()

    @action(detail=True, methods=['patch'], url_path='mark-paid', permission_classes=[IsAdmin])
    def mark_paid(self, request, pk=None):
        invoice = self.get_object()
        if invoice.status == 'paid':
            return Response({'error': 'Invoice already paid'}, status=400)
        invoice.status = 'paid'
        invoice.paid_at = timezone.now()
        invoice.save()
        return Response({'message': 'Invoice marked as paid'})