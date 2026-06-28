from django_eventstream import send_event
from .models import Notification, NotificationType
from .tasks import send_notification_email


# Notification types that also trigger an email
EMAIL_NOTIFICATION_TYPES = {
    NotificationType.PROJECT_ASSIGNED,
    NotificationType.STATUS_UPDATE,
    NotificationType.INVOICE_EVENT,
}


def notify(recipient, notification_type, title, message, actor=None, link=''):
    """
    Central function to create and dispatch a notification.

    Usage:
        from notifications.service import notify
        from notifications.models import NotificationType

        notify(
            recipient=user,
            notification_type=NotificationType.PROJECT_ASSIGNED,
            title="New Project Assigned",
            message="You have been assigned to PRJ-001",
            actor=request.user,
            link="/projects/PRJ-001"
        )
    """
    notification = Notification.objects.create(
        recipient=recipient,
        actor=actor,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link,
    )

    _push_sse(notification)
    _maybe_send_email(notification)

    return notification


def _push_sse(notification):
    """Push to recipient's private SSE channel."""
    channel = f'notifications-{notification.recipient.user_id}'
    payload = {
        'id':           str(notification.id),
        'type':         notification.notification_type,
        'title':        notification.title,
        'message':      notification.message,
        'link':         notification.link,
        'is_read':      notification.is_read,
        'created_at':   notification.created_at.isoformat(),
    }

    send_event(channel, 'notification', payload)

def _maybe_send_email(notification):
    if notification.notification_type in EMAIL_NOTIFICATION_TYPES:
        send_notification_email.delay(
            recipient_email=notification.recipient.email,
            title=notification.title,
            message=notification.message,
            link=notification.link,
        )
        
        
def build_portal_link(user, path):
    """Build a role-aware portal link for a user."""
    role_prefix = {
        'admin': '/portal/admin',
        'staff': '/portal/staff',
        'client': '/portal/client',
    }
    prefix = role_prefix.get(user.role, '/portal')
    return f"{prefix}{path}"