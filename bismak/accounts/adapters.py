import os
from allauth.account.adapter import DefaultAccountAdapter

class CustomAccountAdapter(DefaultAccountAdapter):
    def get_email_confirmation_url(self, request, emailconfirmation):
        key = emailconfirmation.key
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
        return f"{frontend_url}/portal/verify-email/{key}"