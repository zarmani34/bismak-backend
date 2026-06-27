from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_notification_email(self, recipient_email, title, message, link):
    try:
        import resend
        from django.conf import settings

        resend.api_key = settings.RESEND_API_KEY

        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body style="margin:0;padding:0;background-color:#0a0a1a;font-family:Arial,sans-serif;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#0a0a1a;padding:40px 20px;">
                <tr>
                    <td align="center">
                        <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">
                            
                            <!-- Header -->
                            <tr>
                                <td style="background:linear-gradient(135deg,#1a1a3e,#2a2a5e);padding:30px;border-radius:12px 12px 0 0;text-align:center;">
                                    <h1 style="color:#e8a317;margin:0;font-size:24px;font-weight:700;letter-spacing:1px;">BISMAK EXCEL</h1>
                                    <p style="color:#a0a0c0;margin:8px 0 0 0;font-size:13px;">Technical Services</p>
                                </td>
                            </tr>

                            <!-- Body -->
                            <tr>
                                <td style="background:#12122a;padding:40px 30px;">
                                    <h2 style="color:#ffffff;margin:0 0 16px 0;font-size:20px;">{title}</h2>
                                    <p style="color:#c0c0d8;margin:0 0 24px 0;font-size:15px;line-height:1.6;">{message}</p>
                                    
                                    {f'''
                                    <table cellpadding="0" cellspacing="0">
                                        <tr>
                                            <td style="background:#e8a317;border-radius:8px;padding:14px 28px;">
                                                <a href="{settings.FRONTEND_URL}{link}" 
                                                   style="color:#ffffff;text-decoration:none;font-weight:700;font-size:15px;">
                                                    View Details →
                                                </a>
                                            </td>
                                        </tr>
                                    </table>
                                    ''' if link else ''}
                                </td>
                            </tr>

                            <!-- Footer -->
                            <tr>
                                <td style="background:#0d0d20;padding:20px 30px;border-radius:0 0 12px 12px;text-align:center;border-top:1px solid #2a2a4a;">
                                    <p style="color:#606080;font-size:12px;margin:0;">
                                        This is an automated notification from BISMAK Excel Technical Services.<br>
                                        © 2026 BISMAK Excel. All rights reserved.
                                    </p>
                                </td>
                            </tr>

                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

        params = {
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": [recipient_email],
            "subject": f"BISMAK | {title}",
            "html": body_html,
        }

        resend.Emails.send(params)
        logger.info(f"Notification email sent to {recipient_email}")

    except Exception as exc:
        logger.error(f"Notification email failed: {exc}")
        raise self.retry(exc=exc)