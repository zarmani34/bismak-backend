from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_notification_email(self, recipient_email, title, message, link):
    """
    Sends a notification email to the recipient.
    Retries up to 3 times if it fails, waiting 60 seconds between retries.
    """
    try:
        body = f"{message}"
        if link:
            body += f"\n\nView details: {settings.FRONTEND_URL}{link}"

        send_mail(
            subject=title,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
    except Exception as exc:
        raise self.retry(exc=exc)