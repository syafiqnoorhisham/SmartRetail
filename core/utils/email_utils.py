"""
Email utilities for SmartRetail Dashboard using SendGrid HTTP API
This bypasses Railway's SMTP restrictions by using HTTPS instead of SMTP
"""

from django.conf import settings
from django.template.loader import render_to_string
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

logger = logging.getLogger(__name__)


def send_employee_invitation(employee_data, invitation_token):
    """
    Send invitation email to a new employee using SendGrid HTTP API
    
    Args:
        employee_data: Dictionary containing employee information
            - name: Employee's full name
            - email: Employee's email address
            - employee_id: Generated employee ID
            - role: Employee role
        invitation_token: Unique token for the invitation link
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Get settings
        app_url = getattr(settings, 'APP_URL', 'http://localhost:8000')
        app_url = app_url.rstrip('/')
        
        sendgrid_api_key = getattr(settings, 'SENDGRID_API_KEY', None)
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@smartretail.com')
        
        if not sendgrid_api_key:
            logger.error("❌ SENDGRID_API_KEY not configured")
            return False
        
        # Build invitation URL
        invitation_url = f"{app_url}/invitation/accept/{invitation_token}/"
        
        logger.info(f"📧 Preparing email for {employee_data['email']}")
        logger.info(f"🔗 Invitation URL: {invitation_url}")
        logger.info(f"📡 Using SendGrid HTTP API (not SMTP)")
        
        # Email subject
        subject = f"Welcome to SmartRetail - Complete Your Registration"
        
        # Email context
        context = {
            'employee_name': employee_data['name'],
            'employee_id': employee_data['employee_id'],
            'role': employee_data['role'],
            'invitation_url': invitation_url,
            'company_name': 'SmartRetail',
            'app_url': app_url,
        }
        
        # Render HTML email
        html_content = render_to_string('emails/employee_invitation.html', context)
        
        # Plain text fallback
        plain_content = f"""
Hello {employee_data['name']},

Welcome to SmartRetail!

You have been added as a {employee_data['role']} to our system.

Your Employee ID: {employee_data['employee_id']}

To complete your registration and set your password, please click the link below:

{invitation_url}

This link will expire in 48 hours.

If you did not expect this invitation, please ignore this email.

Best regards,
SmartRetail Team
        """.strip()
        
        # Create SendGrid message
        message = Mail(
            from_email=from_email,
            to_emails=employee_data['email'],
            subject=subject,
            plain_text_content=plain_content,
            html_content=html_content
        )
        
        # Send email via SendGrid HTTP API
        logger.info(f"📤 Sending email via SendGrid HTTP API to {employee_data['email']}...")
        
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        
        if response.status_code in [200, 201, 202]:
            logger.info(f"✅ Invitation email sent successfully to {employee_data['email']} (status: {response.status_code})")
            return True
        else:
            logger.error(f"❌ SendGrid returned status {response.status_code}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Failed to send invitation email to {employee_data['email']}: {type(e).__name__} - {str(e)}")
        return False


def send_invitation_async(employee_data, invitation_token):
    """
    Wrapper function for async email sending
    This is called from a background thread
    """
    try:
        result = send_employee_invitation(employee_data, invitation_token)
        if result:
            logger.info(f"✅ [ASYNC] Email sent successfully to {employee_data['email']}")
        else:
            logger.warning(f"⚠️ [ASYNC] Email failed to send to {employee_data['email']}")
        return result
    except Exception as e:
        logger.error(f"❌ [ASYNC] Error in background email sending: {str(e)}")
        return False


def resend_invitation(employee_data, new_token):
    """
    Resend invitation email with a new token
    
    Args:
        employee_data: Dictionary containing employee information
        new_token: New invitation token
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    return send_employee_invitation(employee_data, new_token)
