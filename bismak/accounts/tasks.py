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

        adapter = DefaultAccountAdapter()
        msg = adapter.render_mail(template_prefix, email, context)

        resend.api_key = settings.RESEND_API_KEY

        # Extract confirmation URL from message body
        body_text = msg.body
        confirm_url = context.get('activate_url', context.get('password_reset_url', ''))

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
                                    <h2 style="color:#ffffff;margin:0 0 16px 0;font-size:20px;">{msg.subject}</h2>
                                    <p style="color:#c0c0d8;margin:0 0 24px 0;font-size:15px;line-height:1.6;white-space:pre-line;">{body_text}</p>
                                    
                                    {f'''
                                    <table cellpadding="0" cellspacing="0">
                                        <tr>
                                            <td style="background:#e8a317;border-radius:8px;padding:14px 28px;">
                                                <a href="{confirm_url}" 
                                                   style="color:#ffffff;text-decoration:none;font-weight:700;font-size:15px;">
                                                    Verify Email →
                                                </a>
                                            </td>
                                        </tr>
                                    </table>
                                    ''' if confirm_url else ''}
                                </td>
                            </tr>

                            <!-- Footer -->
                            <tr>
                                <td style="background:#0d0d20;padding:20px 30px;border-radius:0 0 12px 12px;text-align:center;border-top:1px solid #2a2a4a;">
                                    <p style="color:#606080;font-size:12px;margin:0;">
                                        This is an automated message from BISMAK Excel Technical Services.<br>
                                        If you did not request this, please ignore this email.<br>
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
            "to": [email],
            "subject": msg.subject,
            "html": body_html,
        }

        resend.Emails.send(params)
        logger.info(f"Email sent successfully to {email}")

    except Exception as exc:
        logger.error(f"Email failed: {exc}")
        raise self.retry(exc=exc)