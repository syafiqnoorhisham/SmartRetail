"""
Email utilities for SmartRetail Dashboard
Handles sending invitation emails to new employees
WITH INCREASED TIMEOUT AND RETRY LOGIC FOR RAILWAY
"""

from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging
import socket
import time

logger = logging.getLogger(__name__)


def send_employee_invitation(employee_data, invitation_token, timeout_seconds=30, max_retries=2):
    """
    Send invitation email to a new employee with timeout handling and retry logic
    
    Args:
        employee_data: Dictionary containing employee information
            - name: Employee's full name
            - email: Employee's email address
            - employee_id: Generated employee ID
            - role: Employee role
        invitation_token: Unique token for the invitation link
        timeout_seconds: Socket timeout in seconds (default: 30 for Railway)
        max_retries: Maximum number of retry attempts (default: 2)
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    original_timeout = socket.getdefaulttimeout()
    
    # Get settings
    app_url = getattr(settings, 'APP_URL', 'http://localhost:8000')
    app_url = app_url.rstrip('/')
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@smartretail.com')
    
    # Build invitation URL
    invitation_url = f"{app_url}/invitation/accept/{invitation_token}/"
    
    logger.info(f"📧 Preparing email for {employee_data['email']}")
    logger.info(f"🔗 Invitation URL: {invitation_url}")
    logger.info(f"📡 Email Host: {settings.EMAIL_HOST}")
    logger.info(f"🔑 Email User: {settings.EMAIL_HOST_USER}")
    
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
    
    # Retry logic
    for attempt in range(max_retries + 1):
        try:
            # Set socket timeout to prevent hanging
            socket.setdefaulttimeout(timeout_seconds)
            
            if attempt > 0:
                logger.info(f"🔄 Retry attempt {attempt}/{max_retries} for {employee_data['email']}")
                time.sleep(2)  # Wait 2 seconds between retries
            
            # Create email message
            email = EmailMessage(
                subject=subject,
                body=html_message,
                from_email=from_email,
                to=[employee_data['email']]
            )
            email.content_subtype = "html"  # Main content is HTML
            
            # Send email with timeout protection
            logger.info(f"📤 Sending email to {employee_data['email']} (timeout: {timeout_seconds}s)...")
            start_time = time.time()
            
            email.send(fail_silently=False)
            
            elapsed = time.time() - start_time
            logger.info(f"✅ Invitation email sent successfully to {employee_data['email']} in {elapsed:.2f}s")
            return True
            
        except socket.timeout:
            logger.error(f"⏱️ TIMEOUT: Email sending timed out after {timeout_seconds}s for {employee_data['email']} (attempt {attempt + 1}/{max_retries + 1})")
            if attempt == max_retries:
                logger.error(f"❌ All retry attempts exhausted for {employee_data['email']}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Failed to send invitation email to {employee_data['email']}: {type(e).__name__} - {str(e)} (attempt {attempt + 1}/{max_retries + 1})")
            if attempt == max_retries:
                logger.error(f"❌ All retry attempts exhausted for {employee_data['email']}")
                return False
        
        finally:
            # Always restore original timeout
            socket.setdefaulttimeout(original_timeout)
    
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
