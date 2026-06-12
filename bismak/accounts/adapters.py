import os
from allauth.account.adapter import DefaultAccountAdapter


class CustomAccountAdapter(DefaultAccountAdapter):

    def get_email_confirmation_url(self, request, emailconfirmation):
        key = emailconfirmation.key
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
        return f"{frontend_url}/portal/verify-email/{key}"

    def send_mail(self, template_prefix, email, context):
        from accounts.tasks import send_allauth_email_task

        # Serialize context — remove non-JSON-serializable objects
        safe_context = {}
        for key, value in context.items():
            try:
                import json
                json.dumps(value)
                safe_context[key] = value
            except (TypeError, ValueError):
                # Convert non-serializable objects to string
                safe_context[key] = str(value)

        send_allauth_email_task.delay(template_prefix, email, safe_context)