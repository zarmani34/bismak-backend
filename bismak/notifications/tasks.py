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
    
    
#     from celery import shared_task
# from django.conf import settings
# import resend


# @shared_task(bind=True, max_retries=3, default_retry_delay=60)
# def send_notification_email(self, recipient_email, title, message, link):
#     try:
#         resend.api_key = settings.RESEND_API_KEY

#         body_html = f"""
#         <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
#             <div style="background: #1a1a2e; padding: 20px; border-radius: 8px;">
#                 <h2 style="color: #ffffff; margin: 0 0 16px 0;">{title}</h2>
#                 <p style="color: #cccccc; margin: 0 0 16px 0;">{message}</p>
#                 {f'<a href="{settings.FRONTEND_URL}{link}" style="display: inline-block; background: #e8a317; color: #ffffff; padding: 10px 20px; border-radius: 6px; text-decoration: none;">View Details</a>' if link else ''}
#             </div>
#             <p style="color: #999999; font-size: 12px; margin-top: 16px;">
#                 This is an automated notification from BISMAK Excel Technical Services.
#             </p>
#         </div>
#         """

#         params = {
#             "from": settings.DEFAULT_FROM_EMAIL,
#             "to": [recipient_email],
#             "subject": title,
#             "html": body_html,
#         }

#         resend.Emails.send(params)

#     except Exception as exc:
#         raise self.retry(exc=exc)