from django.db import models
from commmon.models import UUIDTimeStampedModel
from rest_framework.exceptions import ValidationError
from accounts.models import User
from projects.models import Project

# Create your models here.
class ServiceRequestChoice(models.TextChoices):
    PENDING = "pending", "Pending"
    REVIEWED = "reviewed", "Reviewed"
    QUOTED = "quoted", "Quoted"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETED = "completed", "Completed"

class ServiceType(UUIDTimeStampedModel):
    name = models.CharField(max_length=255)  # e.g Fire Certificate, Site Survey
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)  # admin can deactivate types

    def __str__(self):
        return self.name

class ServiceRequest(UUIDTimeStampedModel):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='service_requests')    
    name = models.CharField(max_length=50)
    service_type = models.ForeignKey(ServiceType, on_delete=models.PROTECT, null=True, blank=True, related_name='requests')
    custom_service = models.CharField(max_length=255, blank=True)  # for one-off services
    location = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=ServiceRequestChoice.choices, default='pending')

    def get_service_name(self):
        return self.service_type.name if self.service_type else self.custom_service

    def __str__(self):
        return f"{self.owner.get_full_name()} — {self.service_type.name}"