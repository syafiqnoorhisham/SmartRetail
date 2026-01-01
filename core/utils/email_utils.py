"""
Email utilities for SmartRetail Dashboard using Brevo HTTP API
This bypasses Railway's SMTP restrictions by using HTTPS instead of SMTP
"""

from django.conf import settings
from django.template.loader import render_to_string
import logging
import requests

logger = logging.getLogger(__name__)


def send_employee_invitation(employee_data, invitation_token):
    """
    Send invitation email to a new employee using Brevo HTTP API
    
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
        
        brevo_api_key = getattr(settings, 'BREVO_API_KEY', None)
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@smartretail.com')
        from_name = getattr(settings, 'DEFAULT_FROM_NAME', 'SmartRetail')
        
        if not brevo_api_key:
            logger.error("❌ BREVO_API_KEY not configured")
            return False
        
        # Build invitation URL
        invitation_url = f"{app_url}/invitation/accept/{invitation_token}/"
        
        logger.info(f"📧 Preparing email for {employee_data['email']}")
        logger.info(f"🔗 Invitation URL: {invitation_url}")
        logger.info(f"📡 Using Brevo HTTP API")
        
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
        
        # Parse from_email to extract name and email
        if '<' in from_email and '>' in from_email:
            from_name = from_email.split('<')[0].strip()
            from_email_addr = from_email.split('<')[1].replace('>', '').strip()
        else:
            from_email_addr = from_email
        
        # Send email via Brevo HTTP API
        logger.info(f"📤 Sending email via Brevo HTTP API to {employee_data['email']}...")
        
        response = requests.post(
            'https://api.brevo.com/v3/smtp/email',
            headers={
                'api-key': brevo_api_key,
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            json={
                'sender': {
                    'name': from_name,
                    'email': from_email_addr
                },
                'to': [
                    {
                        'email': employee_data['email'],
                        'name': employee_data['name']
                    }
                ],
                'subject': subject,
                'htmlContent': html_content,
                'textContent': plain_content
            },
            timeout=30
        )
        
        if response.status_code in [200, 201, 202]:
            logger.info(f"✅ Invitation email sent successfully to {employee_data['email']} (status: {response.status_code})")
            return True
        else:
            logger.error(f"❌ Brevo returned status {response.status_code}: {response.text}")
            return False
        
    except requests.exceptions.Timeout:
        logger.error(f"⏱️ TIMEOUT: Email sending timed out for {employee_data['email']}")
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
