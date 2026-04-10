# apps/billing/serializers.py
from rest_framework import serializers
from .models import Quote, Invoice
from accounts.models import User
from accounts.serializers import UserSerializer


class InvoiceSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id', 'code', 'amount', 'status', 'status_display',
            'due_date', 'paid_at', 'note', 'created_at'
        ]
        read_only_fields = ['id', 'code', 'created_at']


class QuoteListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    quoted_by = UserSerializer()
    owner = serializers.SerializerMethodField()
    project = serializers.CharField(source="project.code", read_only=True)
    service_request = serializers.CharField(source="service_request.code", read_only=True)
    

    def get_owner(self, obj):
        if obj.service_request:
            return UserSerializer(obj.service_request.owner).data
        elif obj.project:
            return UserSerializer(obj.project.owner).data
        return None

    class Meta:
        model = Quote
        fields = [
            'id', 'code', 'service_request',  'owner', 'project', 'amount', 'status', 'status_display',
            'valid_until', 'quoted_by', 'created_at'
        ]


class QuoteDetailSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    quoted_by = UserSerializer()
    invoice = InvoiceSerializer(read_only=True)
    owner = serializers.SerializerMethodField()
    project = serializers.CharField(source="project.code", read_only=True)
    service_request = serializers.CharField(source="service_request.code", read_only=True)

    def get_owner(self, obj):
        if obj.service_request:
            return UserSerializer(obj.service_request.owner).data
        elif obj.project:
            return UserSerializer(obj.project.owner).data
        return None


    class Meta:
        model = Quote
        fields = [
            'id', 'code',  'owner', 'amount', 'note', 'status', 'status_display',
            'valid_until', 'accepted_at', 'rejected_at',
            'quoted_by', 'invoice', 'created_at', 'updated_at', 'service_request', 'project',
        ]
        read_only_fields = [
            'id', 'code', 'quoted_by', 'accepted_at',
            'rejected_at', 'created_at', 'updated_at', 'service_request', 'project',
        ]
