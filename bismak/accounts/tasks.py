from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_allauth_email_task(self, template_prefix, email, context):
    logger.info(f"Sending email to {email} with template {template_prefix}")
    try:
        import resend
        from django.conf import settings
        from allauth.account.adapter import DefaultAccountAdapter

        # Render email content using allauth's templates
        adapter = DefaultAccountAdapter()
        msg = adapter.render_mail(template_prefix, email, context)

        resend.api_key = settings.RESEND_API_KEY

        params = {
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": [email],
            "subject": msg.subject,
            "html": msg.body if '<html' in msg.body else f"<p>{msg.body}</p>",
        }

        resend.Emails.send(params)
        logger.info(f"Email sent successfully to {email}")

    except Exception as exc:
        logger.error(f"Email failed: {exc}")
        raise self.retry(exc=exc)
    