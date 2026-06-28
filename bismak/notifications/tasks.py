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
            <html lang="en">
            <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <meta http-equiv="X-UA-Compatible" content="IE=edge">
            <title>{title}</title>
            </head>
            <body style="margin:0;padding:0;background-color:#f8f8f6;font-family:'Segoe UI',Arial,sans-serif;">
            
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" 
                    style="background-color:#f8f8f6;padding:48px 16px;">
                <tr>
                <td align="center">
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" 
                        style="max-width:580px;width:100%;">

                    <!-- Header -->
                    <tr>
                        <td style="background-color:#37574a;padding:32px 40px;
                                border-radius:12px 12px 0 0;text-align:center;">
                        <p style="margin:0 0 4px 0;color:#4a6b5c;font-size:11px;
                                    letter-spacing:3px;text-transform:uppercase;font-weight:600;">
                            Portal Notification
                        </p>
                        <h1 style="margin:0;color:#F6F5D9;font-size:26px;font-weight:700;
                                    letter-spacing:1.5px;text-transform:uppercase;">
                            BISMAK EXCEL
                        </h1>
                        <p style="margin:6px 0 0 0;color:#4a6b5c;font-size:11px;
                                    letter-spacing:2px;text-transform:uppercase;">
                            Technical Services
                        </p>
                        </td>
                    </tr>

                    <!-- Accent bar -->
                    <tr>
                        <td style="background-color:#D95C3E;height:4px;font-size:0;line-height:0;">
                        &nbsp;
                        </td>
                    </tr>

                    <!-- Body -->
                    <tr>
                        <td style="background-color:#ffffff;padding:40px 40px 32px 40px;
                                border-left:1px solid #e0ddc7;border-right:1px solid #e0ddc7;">
                        
                        <!-- Notification type label -->
                        <p style="margin:0 0 20px 0;display:inline-block;
                                    background-color:#f8f8f6;border:1px solid #e0ddc7;
                                    color:#37574a;font-size:11px;font-weight:700;
                                    letter-spacing:2px;text-transform:uppercase;
                                    padding:6px 14px;border-radius:4px;">
                            New Notification
                        </p>

                        <h2 style="margin:0 0 14px 0;color:#333333;font-size:22px;
                                    font-weight:700;line-height:1.3;">
                            {title}
                        </h2>
                        
                        <p style="margin:0 0 32px 0;color:#4a4a4a;font-size:15px;
                                    line-height:1.75;border-left:3px solid #D95C3E;
                                    padding-left:16px;">
                            {message}
                        </p>

                        {f'''
                        <!-- CTA Button -->
                        <table role="presentation" cellpadding="0" cellspacing="0">
                            <tr>
                            <td style="background-color:#D95C3E;border-radius:8px;">
                                <a href="{settings.FRONTEND_URL}{link}"
                                style="display:inline-block;padding:14px 32px;
                                        color:#F6F5D9;text-decoration:none;
                                        font-size:14px;font-weight:700;
                                        letter-spacing:0.5px;text-transform:uppercase;">
                                View Details &rarr;
                                </a>
                            </td>
                            </tr>
                        </table>
                        ''' if link else ''}

                        </td>
                    </tr>

                    <!-- Divider -->
                    <tr>
                        <td style="background-color:#ffffff;padding:0 40px;
                                border-left:1px solid #e0ddc7;border-right:1px solid #e0ddc7;">
                        <div style="border-top:1px solid #e0ddc7;"></div>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color:#2a4238;padding:28px 40px;
                                border-radius:0 0 12px 12px;text-align:center;">
                        <p style="margin:0 0 8px 0;color:#F6F5D9;font-size:13px;font-weight:600;">
                            BISMAK Excel Technical Services
                        </p>
                        <p style="margin:0;color:#4a6b5c;font-size:11px;line-height:1.6;">
                            This is an automated notification from your BISMAK portal.<br>
                            Please do not reply to this email.<br>
                            &copy; 2026 BISMAK Excel. All rights reserved.
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