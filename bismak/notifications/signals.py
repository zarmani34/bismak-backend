
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from projects.models import Project, ProjectAssignment
from services.models import ServiceRequest
from equipments.models import EquipmentRequest
from billings.models import Invoice, Quote

from .service import notify
from .models import NotificationType

User = get_user_model()


# ─── Helper ──────────────────────────────────────────────────────────────────

def get_all_admins():
    """Returns all active admin users."""
    return User.objects.filter(role='admin', is_active=True)


# ─── Projects ────────────────────────────────────────────────────────────────

@receiver(post_save, sender=Project)
def on_project_created(sender, instance, created, **kwargs):
    """Notify all admins when a new project is created."""
    if not created:
        return
    
    for admin in get_all_admins():
        notify(
            recipient=admin,
            notification_type=NotificationType.PROJECT_ASSIGNED,
            title="New Project Created",
            message=f"{instance.owner.get_full_name()} created a new project {instance.code} — {instance.company}.",
            actor=instance.owner,
            link=f"/projects/{instance.code}",
        )

@receiver(post_save, sender=ProjectAssignment)
def on_project_assignment_created(sender, instance, created, **kwargs):
    """
    When a staff is assigned to a project:
    - Notify the assigned staff member
    - Notify the project owner (client)
    """
    if not created:
        return

    project = instance.project
    assignee = instance.assignee
    assigned_by = instance.assigned_by

    # Notify the staff member assigned
    notify(
        recipient=assignee,
        notification_type=NotificationType.PROJECT_ASSIGNED,
        title="You've Been Assigned to a Project",
        message=f"You have been assigned to project {project.code} — {project.company}.",
        actor=assigned_by,
        link=f"/projects/{project.code}",
    )

    # Notify the project owner (client)
    if project.owner:
        notify(
            recipient=project.owner,
            notification_type=NotificationType.PROJECT_ASSIGNED,
            title="Your Project Has Been Assigned",
            message=f"A team member has been assigned to work on your project {project.code}.",
            actor=assigned_by,
            link=f"/projects/{project.code}",
        )


@receiver(post_save, sender=Project)
def on_project_status_changed(sender, instance, created, **kwargs):
    """
    When a project status changes:
    - Notify the project owner (client)
    """
    if created:
        return

    if not instance.tracker.has_changed('status'):
        return

    if not instance.owner:
        return

    notify(
        recipient=instance.owner,
        notification_type=NotificationType.STATUS_UPDATE,
        title="Project Status Updated",
        message=f"Your project {instance.code} status has been updated to: {instance.get_status_display()}.",
        link=f"/projects/{instance.code}",
    )


# ─── Service Requests ────────────────────────────────────────────────────────

@receiver(post_save, sender=ServiceRequest)
def on_service_request_created(sender, instance, created, **kwargs):
    """
    When a client submits a service request:
    - Notify all admins
    """
    if not created:
        return

    for admin in get_all_admins():
        notify(
            recipient=admin,
            notification_type=NotificationType.NEW_MESSAGE,
            title="New Service Request Submitted",
            message=f"{instance.owner.get_full_name()} submitted a service request ({instance.code}) for {instance.get_service_name()}.",
            actor=instance.owner,
            link=f"/services/{instance.code}",
        )


@receiver(post_save, sender=ServiceRequest)
def on_service_request_status_changed(sender, instance, created, **kwargs):
    """
    When a service request status changes:
    - Notify the client who submitted it
    """
    if created:
        return

    if not instance.tracker.has_changed('status'):
        return

    notify(
        recipient=instance.owner,
        notification_type=NotificationType.STATUS_UPDATE,
        title="Service Request Updated",
        message=f"Your service request {instance.code} status has been updated to: {instance.get_status_display()}.",
        link=f"/services/{instance.code}",
    )


# ─── Equipment Requests ───────────────────────────────────────────────────────

@receiver(post_save, sender=EquipmentRequest)
def on_equipment_request_created(sender, instance, created, **kwargs):
    """
    When a staff submits an equipment request:
    - Notify all admins
    """
    if not created:
        return

    for admin in get_all_admins():
        notify(
            recipient=admin,
            notification_type=NotificationType.NEW_MESSAGE,
            title="New Equipment Request",
            message=f"{instance.requested_by.get_full_name()} requested {instance.equipment.name} ({instance.code}).",
            actor=instance.requested_by,
            link=f"/equipments/requests/{instance.code}",
        )


@receiver(post_save, sender=EquipmentRequest)
def on_equipment_request_status_changed(sender, instance, created, **kwargs):
    """
    When an equipment request is approved or rejected:
    - Notify the staff member who requested it
    """
    if created:
        return

    if not instance.tracker.has_changed('status'):
        return

    if not instance.requested_by:
        return

    status_display = dict(EquipmentRequest.STATUS_CHOICES).get(instance.status, instance.status)

    notify(
        recipient=instance.requested_by,
        notification_type=NotificationType.STATUS_UPDATE,
        title="Equipment Request Updated",
        message=f"Your equipment request {instance.code} for {instance.equipment.name} has been {status_display.lower()}.",
        actor=instance.approved_by,
        link=f"/equipments/requests/{instance.code}",
    )


# ─── Billing ─────────────────────────────────────────────────────────────────

@receiver(post_save, sender=Invoice)
def on_invoice_created(sender, instance, created, **kwargs):
    """
    When an invoice is created:
    - Notify the client (via quote → project/service request owner)
    """
    if not created:
        return

    recipient = _get_invoice_recipient(instance)
    if not recipient:
        return

    notify(
        recipient=recipient,
        notification_type=NotificationType.INVOICE_EVENT,
        title="New Invoice Issued",
        message=f"A new invoice {instance.code} of ₦{instance.amount} has been issued to you. Due date: {instance.due_date}.",
        link=f"/billing/invoices/{instance.code}",
    )


@receiver(post_save, sender=Invoice)
def on_invoice_paid(sender, instance, created, **kwargs):
    """
    When an invoice status changes to paid:
    - Notify all admins
    """
    if created:
        return

    if not instance.tracker.has_changed('status'):
        return

    if instance.status != 'paid':
        return

    for admin in get_all_admins():
        notify(
            recipient=admin,
            notification_type=NotificationType.INVOICE_EVENT,
            title="Invoice Payment Received",
            message=f"Invoice {instance.code} of ₦{instance.amount} has been marked as paid.",
            link=f"/billing/invoices/{instance.code}",
        )


@receiver(post_save, sender=Quote)
def on_quote_sent(sender, instance, created, **kwargs):
    """
    When a quote is created (sent to client):
    - Notify the client
    """
    if not created:
        return

    recipient = _get_quote_recipient(instance)
    if not recipient:
        return

    notify(
        recipient=recipient,
        notification_type=NotificationType.INVOICE_EVENT,
        title="You've Received a Quote",
        message=f"A quote {instance.code} of ₦{instance.amount} has been sent to you. Valid until: {instance.valid_until}.",
        actor=instance.quoted_by,
        link=f"/billing/quotes/{instance.code}",
    )


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _get_invoice_recipient(invoice):
    """Get the client from invoice → quote → project/service request."""
    if not invoice.quote:
        return None
    quote = invoice.quote
    if quote.project and quote.project.owner:
        return quote.project.owner
    if quote.service_request and quote.service_request.owner:
        return quote.service_request.owner
    return None


def _get_quote_recipient(quote):
    """Get the client from quote → project/service request."""
    if quote.project and quote.project.owner:
        return quote.project.owner
    if quote.service_request and quote.service_request.owner:
        return quote.service_request.owner
    return None