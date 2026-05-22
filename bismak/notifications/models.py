from django.db import models
from django.db import models
from django.conf import settings
from commmon.models import UUIDTimeStampedModel

# Create your models here.


class NotificationType(models.TextChoices):
    PROJECT_ASSIGNED   = 'project_assigned',   'Project Assigned'
    STATUS_UPDATE      = 'status_update',       'Status Update'
    DOCUMENT_UPLOADED  = 'document_uploaded',   'Document Uploaded'
    NEW_MESSAGE        = 'new_message',         'New Message'
    INVOICE_EVENT      = 'invoice_event',       'Invoice Event'


class Notification(UUIDTimeStampedModel):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='sent_notifications'
    )
    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices
    )
    title   = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    link    = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recipient} — {self.title}"