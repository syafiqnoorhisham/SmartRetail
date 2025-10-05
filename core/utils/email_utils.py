"""
Email utilities for SmartRetail Dashboard
Handles sending invitation emails to new employees
WITH TIMEOUT HANDLING AND ERROR RECOVERY
"""

from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging
import socket

logger = logging.getLogger(__name__)


def send_employee_invitation(employee_data, invitation_token, timeout_seconds=10):
    """
    Send invitation email to a new employee with timeout handling
    
    Args:
        employee_data: Dictionary containing employee information
            - name: Employee's full name
            - email: Employee's email address
            - employee_id: Generated employee ID
            - role: Employee role
        invitation_token: Unique token for the invitation link
        timeout_seconds: Socket timeout in seconds (default: 10)
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    original_timeout = socket.getdefaulttimeout()
    
    try:
        # Set socket timeout to prevent hanging
        socket.setdefaulttimeout(timeout_seconds)
        
        # Get settings
        app_url = getattr(settings, 'APP_URL', 'http://localhost:8000')
        # Remove trailing slash if present
        app_url = app_url.rstrip('/')
        
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@smartretail.com')
        
        # Build invitation URL
        invitation_url = f"{app_url}/invitation/accept/{invitation_token}/"
        
        logger.info(f"📧 Preparing email for {employee_data['email']}")
        logger.info(f"🔗 Invitation URL: {invitation_url}")
        
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
        html_message = render_to_string('emails/employee_invitation.html', context)
        
        # Plain text fallback
        plain_message = f"""
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
        
        # Create email message
        email = EmailMessage(
            subject=subject,
            body=html_message,
            from_email=from_email,
            to=[employee_data['email']]
        )
        email.content_subtype = "html"  # Main content is HTML
        
        # Send email with timeout protection
        logger.info(f"📤 Sending email to {employee_data['email']}...")
        email.send(fail_silently=False)
        
        logger.info(f"✅ Invitation email sent successfully to {employee_data['email']} ({employee_data['employee_id']})")
        return True
        
    except socket.timeout:
        logger.error(f"⏱️ TIMEOUT: Email sending timed out after {timeout_seconds}s for {employee_data['email']}")
        return False
        
    except Exception as e:
        logger.error(f"❌ Failed to send invitation email to {employee_data['email']}: {type(e).__name__} - {str(e)}")
        return False
        
    finally:
        # Always restore original timeout
        socket.setdefaulttimeout(original_timeout)


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
