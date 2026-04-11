from django.db import models
from commmon.models import UUIDTimeStampedModel

# Create your models here.

class Equipment(UUIDTimeStampedModel):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('in_use', 'In Use'),
        ('under_maintenance', 'Under Maintenance'),
        ('retired', 'Retired'),
    ]

    name = models.CharField(max_length=255)
    category = models.CharField(max_length=255, blank=True)  # just a text field
    serial_number = models.CharField(max_length=100, unique=True)
    model = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    description = models.TextField(blank=True)
    last_maintenance_date = models.DateField(null=True, blank=True)
    next_maintenance_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.serial_number})"


class EquipmentRequest(UUIDTimeStampedModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('returned', 'Returned'),
    ]

    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='requests')
    requested_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, related_name='equipment_requests'
    )
    project = models.ForeignKey(
        'projects.Project', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='equipment_requests'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reason = models.TextField(blank=True)  # why staff needs it
    approved_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='approved_equipment_requests'
    )
    date_needed = models.DateField()
    date_returned = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.requested_by} requested {self.equipment.name}"
    
    class Meta:
        ordering = ['-created_at']


class MaintenanceRequest(UUIDTimeStampedModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    TYPE_CHOICES = [
        ('maintenance', 'Maintenance'),
        ('calibration', 'Calibration'),
        ('repair', 'Repair'),
    ]

    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='maintenance_requests')
    requested_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, related_name='maintenance_requests'
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    description = models.TextField()  # what's wrong / why maintenance needed
    scheduled_date = models.DateField(null=True, blank=True)  # admin sets this
    completed_date = models.DateField(null=True, blank=True)
    next_service_date = models.DateField(null=True, blank=True)  # set on completion
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)  # admin notes

    def __str__(self):
        return f"{self.type} request for {self.equipment.name}"