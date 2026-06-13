from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_allauth_email_task(self, template_prefix, email, context):
    logger.info(f"Sending email to {email} with template {template_prefix}")
    try:
        from allauth.account.adapter import DefaultAccountAdapter
        DefaultAccountAdapter().send_mail(template_prefix, email, context)
        logger.info(f"Email sent successfully to {email}")
    except Exception as exc:
        logger.error(f"Email failed: {exc}")
        raise self.retry(exc=exc)