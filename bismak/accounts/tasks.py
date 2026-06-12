from celery import shared_task


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_allauth_email_task(self, template_prefix, email, context):
    try:
        from allauth.account.adapter import DefaultAccountAdapter
        DefaultAccountAdapter().send_mail(template_prefix, email, context)
    except Exception as exc:
        raise self.retry(exc=exc)