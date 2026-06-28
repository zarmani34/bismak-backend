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
        <html lang="en">
        <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <title>{msg.subject}</title>
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
                        Welcome to
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

                    <h2 style="margin:0 0 14px 0;color:#333333;font-size:22px;
                                font-weight:700;line-height:1.3;">
                        Verify your email address
                    </h2>

                    <p style="margin:0 0 12px 0;color:#4a4a4a;font-size:15px;line-height:1.75;">
                        Thank you for registering with BISMAK Excel Technical Services.
                        To complete your registration and access your client portal,
                        please verify your email address.
                    </p>

                    <p style="margin:0 0 32px 0;color:#8a8a8a;font-size:13px;line-height:1.6;">
                        This verification link expires in 3 days. If you did not create
                        an account, you can safely ignore this email.
                    </p>

                    {f'''
                    <!-- CTA Button -->
                    <table role="presentation" cellpadding="0" cellspacing="0">
                        <tr>
                        <td style="background-color:#D95C3E;border-radius:8px;">
                            <a href="{confirm_url}"
                            style="display:inline-block;padding:16px 40px;
                                    color:#F6F5D9;text-decoration:none;
                                    font-size:14px;font-weight:700;
                                    letter-spacing:0.5px;text-transform:uppercase;">
                            Verify Email &rarr;
                            </a>
                        </td>
                        </tr>
                    </table>

                    <p style="margin:20px 0 0 0;color:#8a8a8a;font-size:12px;">
                        Or copy and paste this link into your browser:<br>
                        <a href="{confirm_url}" style="color:#37574a;word-break:break-all;">
                        {confirm_url}
                        </a>
                    </p>
                    ''' if confirm_url else ''}

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
                        If you did not request this email, no action is required.<br>
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
            "to": [email],
            "subject": msg.subject,
            "html": body_html,
        }

        resend.Emails.send(params)
        logger.info(f"Email sent successfully to {email}")

    except Exception as exc:
        logger.error(f"Email failed: {exc}")
        raise self.retry(exc=exc)