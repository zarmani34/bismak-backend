# apps/billing/serializers.py
from rest_framework import serializers
from .models import Quote, Invoice, QuoteItem
from accounts.models import User
from accounts.serializers import UserSerializer


class InvoiceSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True, source='quote.amount')
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


class QuoteItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuoteItem
        fields = ['id', 'description', 'quantity', 'unit_price', 'total']
        read_only_fields = ['id', 'total']

class QuoteDetailSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    quoted_by = UserSerializer()
    invoice = InvoiceSerializer(read_only=True)
    owner = serializers.SerializerMethodField()
    project = serializers.CharField(source="project.code", read_only=True)
    service_request = serializers.CharField(source="service_request.code", read_only=True)
    items = QuoteItemSerializer(many=True)

    def get_owner(self, obj):
        if obj.service_request:
            return UserSerializer(obj.service_request.owner).data
        elif obj.project:
            return UserSerializer(obj.project.owner).data
        return None
    

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        quote = Quote.objects.create(**validated_data)

        for item_data in items_data:
            QuoteItem.objects.create(quote=quote, **item_data)

        # compute total from items
        quote.compute_total()
        return quote

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                QuoteItem.objects.create(quote=instance, **item_data)
            instance.compute_total()

        return instance


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
