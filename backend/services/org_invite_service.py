"""
Organization Invite Service - Handles sending invite emails for team member invitations.
"""
import os
from typing import Optional

from models import Organization, OrganizationInvite, User
from logging_config import get_logger

logger = get_logger(__name__)


def send_org_invite_email(
    invite: OrganizationInvite,
    org: Organization,
    inviter_name: Optional[str] = None
) -> bool:
    """
    Send invite email to a prospective team member.

    Returns True if email was sent successfully.
    """
    sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    app_name = os.getenv("APP_NAME", "Starter")

    invite_url = f"{frontend_url}/invite/{invite.token}"

    if not sendgrid_api_key:
        logger.info(f"[DEV] Would send org invite to {invite.email}")
        logger.info(f"[DEV] Invite URL: {invite_url}")
        return True

    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail, Email, To, Content

        sg = sendgrid.SendGridAPIClient(api_key=sendgrid_api_key)

        from_email = Email(os.getenv("SENDGRID_FROM_EMAIL", "noreply@example.com"))
        to_email = To(invite.email)

        inviter_text = f" by {inviter_name}" if inviter_name else ""
        subject = f"You've been invited to join {org.name}"

        html_content = f"""
        <html>
        <body style="font-family: system-ui, -apple-system, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9fafb;">
            <div style="background-color: white; border-radius: 16px; padding: 32px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="text-align: center; margin-bottom: 24px;">
                    <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #2563EB, #7C3AED); border-radius: 12px; margin: 0 auto 16px; display: flex; align-items: center; justify-content: center;">
                        <span style="color: white; font-weight: bold; font-size: 24px;">S</span>
                    </div>
                    <h1 style="color: #111827; font-size: 24px; margin: 0;">You're Invited</h1>
                </div>

                <p style="color: #374151; font-size: 16px; line-height: 1.6;">Hi,</p>

                <p style="color: #374151; font-size: 16px; line-height: 1.6;">
                    You've been invited{inviter_text} to join <strong>{org.name}</strong> as a{' ' if invite.role == 'editor' else 'n '}<strong>{invite.role}</strong>.
                </p>

                <p style="color: #374151; font-size: 16px; line-height: 1.6;">
                    As a team member, you'll be able to access the dashboard and collaborate with your organization.
                </p>

                <div style="margin: 32px 0; text-align: center;">
                    <a href="{invite_url}"
                       style="display: inline-block; background: linear-gradient(to right, #3b82f6, #9333ea); color: white; padding: 14px 28px; text-decoration: none; border-radius: 12px; font-weight: 600; font-size: 16px;">
                        Accept Invitation
                    </a>
                </div>

                <p style="color: #6b7280; font-size: 14px; line-height: 1.6;">
                    This invitation expires in 7 days. If you have questions, please contact your administrator.
                </p>

                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;" />

                <p style="color: #9ca3af; font-size: 12px; text-align: center;">
                    {app_name}
                </p>
            </div>
        </body>
        </html>
        """

        message = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=subject,
            html_content=Content("text/html", html_content)
        )

        response = sg.send(message)
        success = response.status_code in [200, 201, 202]

        if success:
            logger.info(f"Sent org invite email to {invite.email} for {org.name}")
        else:
            logger.error(f"Failed to send org invite email: status {response.status_code}")

        return success

    except Exception as e:
        logger.error(f"Failed to send org invite email to {invite.email}: {e}")
        return False
