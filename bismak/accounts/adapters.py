import os
from allauth.account.adapter import DefaultAccountAdapter


class CustomAccountAdapter(DefaultAccountAdapter):
    
    def get_email_confirmation_url(self, request, emailconfirmation):
        key = emailconfirmation.key
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
        return f"{frontend_url}/portal/verify-email/{key}"

    def send_mail(self, template_prefix, email, context):
        """Send allauth emails async via Celery so registration doesn't block."""
        from accounts.tasks import send_allauth_email_task
        send_allauth_email_task.delay(template_prefix, email, context)