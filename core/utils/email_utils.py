"""
Email utilities for SmartRetail Dashboard
Handles sending invitation emails to new employees
"""

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


def send_employee_invitation(employee_data, invitation_token):
    """
    Send invitation email to a new employee
    
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
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@smartretail.com')
        
        # Build invitation URL
        invitation_url = f"{app_url}/invitation/accept/{invitation_token}/"
        
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
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=[employee_data['email']],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Invitation email sent to {employee_data['email']} ({employee_data['employee_id']})")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send invitation email to {employee_data['email']}: {str(e)}")
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
