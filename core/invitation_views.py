"""
Additional views for employee invitation flow
"""

import secrets
import logging
import json
import base64
import re
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
from .supabase_client import get_supabase_client, get_supabase_admin_client
from .utils.email_utils import send_employee_invitation, send_invitation_async
import threading

logger = logging.getLogger(__name__)


# Employee Invitation Views

def invitation_accept_view(request, token):
    """Display invitation acceptance page"""
    try:
        client = get_supabase_client()
        
        # Find employee with this token
        result = client.table('employees')\
            .select('*')\
            .eq('invitation_token', token)\
            .execute()
        
        if not result.data:
            # Invalid token
            return render(request, 'invitation_accept.html', {
                'invitation_valid': False
            })
        
        employee = result.data[0]
        
        # Check if already accepted
        if employee.get('invitation_accepted_at'):
            messages.warning(request, 'This invitation has already been used.')
            return redirect('login')
        
        # Check if expired (48 hours)
        invitation_sent = employee.get('invitation_sent_at')
        if invitation_sent:
            sent_time = datetime.fromisoformat(invitation_sent.replace('Z', '+00:00'))
            expiry_hours = getattr(settings, 'INVITATION_EXPIRY_HOURS', 48)
            if datetime.now(sent_time.tzinfo) - sent_time > timedelta(hours=expiry_hours):
                return render(request, 'invitation_accept.html', {
                    'invitation_valid': False
                })
        
        context = {
            'invitation_valid': True,
            'employee': employee,
            'token': token
        }
        
        return render(request, 'invitation_accept.html', context)
        
    except Exception as e:
        logger.error(f"Invitation accept view error: {str(e)}")
        return render(request, 'invitation_accept.html', {
            'invitation_valid': False
        })


@require_http_methods(["POST"])
def invitation_accept_submit(request, token):
    """Handle invitation acceptance and account creation with auto-verified email"""
    try:
        client = get_supabase_client()
        
        # Get password from form
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        # Validation
        if not password or not confirm_password:
            messages.error(request, 'Password is required')
            return redirect('invitation_accept', token=token)
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return redirect('invitation_accept', token=token)
        
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters')
            return redirect('invitation_accept', token=token)
        
        # Password strength validation
        if not (re.search(r'[A-Z]', password) and 
                re.search(r'[a-z]', password) and 
                re.search(r'[0-9]', password)):
            messages.error(request, 'Password must contain uppercase, lowercase, and numbers')
            return redirect('invitation_accept', token=token)
        
        # Find employee with this token
        result = client.table('employees')\
            .select('*')\
            .eq('invitation_token', token)\
            .execute()
        
        if not result.data:
            messages.error(request, 'Invalid invitation token')
            return redirect('login')
        
        employee = result.data[0]
        
        # Check if already accepted
        if employee.get('invitation_accepted_at'):
            messages.warning(request, 'This invitation has already been used')
            return redirect('login')
        
        # Create Supabase Auth account with auto-verified email
        try:
            # Try using admin client to create user with email already confirmed
            admin_client = get_supabase_admin_client()
            
            if admin_client:
                # Use admin API to create user with pre-verified email
                auth_response = admin_client.auth.admin.create_user({
                    "email": employee['email'],
                    "password": password,
                    "email_confirm": True,  # Auto-verify email - no confirmation needed
                    "user_metadata": {
                        "name": employee['name'],
                        "role": employee['role'],
                        "employee_id": employee['employee_id']
                    }
                })
                
                if not auth_response.user:
                    raise Exception("Failed to create auth user")
                
                logger.info(f"✅ User created with admin API - email auto-verified: {employee['email']}")
                
            else:
                # Admin client not available - fall back to regular signup
                # Note: This will send a confirmation email unless email confirmation is disabled
                logger.warning(f"⚠️ Admin client not available, using regular signup for: {employee['email']}")
                
                auth_response = client.auth.sign_up({
                    "email": employee['email'],
                    "password": password,
                    "options": {
                        "data": {
                            "name": employee['name'],
                            "role": employee['role'],
                            "employee_id": employee['employee_id']
                        }
                    }
                })
                
                if not auth_response.user:
                    raise Exception("Failed to create user account")
                
                logger.warning(f"⚠️ User created via regular signup - may require email confirmation: {employee['email']}")
                
        except Exception as auth_error:
            logger.error(f"❌ Auth error creating user for {employee['email']}: {str(auth_error)}")
            messages.error(request, f'Error creating account: {str(auth_error)}')
            return redirect('invitation_accept', token=token)
        
        # Update employee record
        update_data = {
            'status': 'active',
            'invitation_accepted_at': datetime.now().isoformat(),
            'invitation_token': None  # Clear the token
        }
        
        client.table('employees')\
            .update(update_data)\
            .eq('id', employee['id'])\
            .execute()
        
        logger.info(f"✅ Employee invitation accepted: {employee['employee_id']} - {employee['name']}")
        
        messages.success(request, 'Registration complete! You can now login with your credentials.')
        return redirect('login')
        
    except Exception as e:
        logger.error(f"❌ Invitation accept submit error: {str(e)}")
        messages.error(request, f'Error completing registration: {str(e)}')
        return redirect('invitation_accept', token=token)


# Updated api_add_employee to include invitation sending

@csrf_exempt
@require_http_methods(["POST"])
def api_add_employee_with_invitation(request):
    """API endpoint to add a new employee and send invitation email"""
    if not request.session.get('user_id'):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        # Get form data
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        role = request.POST.get('role', '').strip()
        address = request.POST.get('address', '').strip()
        profile_picture = None
        
        # Validation
        if not name or not email or not role:
            return JsonResponse({'error': 'Name, email, and role are required'}, status=400)
        
        # Validate email format
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_regex, email):
            return JsonResponse({'error': 'Invalid email format'}, status=400)
        
        if role not in ['Manager', 'Supplier', 'Sales']:
            return JsonResponse({'error': 'Invalid role'}, status=400)
        
        client = get_supabase_client()
        
        # Check for duplicate email
        email_check = client.table('employees')\
            .select('email')\
            .eq('email', email)\
            .execute()
        
        if email_check.data:
            return JsonResponse({'error': 'Email already exists'}, status=400)
        
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            file = request.FILES['profile_picture']
            
            # Validate file size (2MB)
            if file.size > 2 * 1024 * 1024:
                return JsonResponse({'error': 'Profile picture must be less than 2MB'}, status=400)
            
            # Convert to base64
            file_content = file.read()
            profile_picture = f"data:{file.content_type};base64,{base64.b64encode(file_content).decode('utf-8')}"
        
        # Generate employee ID
        role_prefixes = {
            'Manager': 'M',
            'Supplier': 'SP',
            'Sales': 'S'
        }
        prefix = role_prefixes.get(role, 'E')
        
        # Get existing employees to find next ID
        employees_result = client.table('employees')\
            .select('employee_id')\
            .like('employee_id', f'{prefix}%')\
            .execute()
        
        existing_ids = [e['employee_id'] for e in employees_result.data] if employees_result.data else []
        next_num = 1
        for i in range(1, 10000):
            test_id = f"{prefix}{i:04d}"
            if test_id not in existing_ids:
                next_num = i
                break
        
        employee_id = f"{prefix}{next_num:04d}"
        
        # Generate invitation token
        invitation_token = secrets.token_urlsafe(32)
        
        # Create employee record with pending status
        employee_data = {
            'employee_id': employee_id,
            'name': name,
            'email': email,
            'role': role,
            'address': address if address else None,
            'profile_picture': profile_picture,
            'status': 'pending',  # Set to pending until they accept invitation
            'invitation_token': invitation_token,
            'invitation_sent_at': datetime.now().isoformat()
        }
        
        result = client.table('employees').insert(employee_data).execute()
        
        logger.info(f"✅ Employee record created: {employee_id} - {name}")
        
        # Send invitation email in background thread (async)
        def send_email_background():
            try:
                logger.info(f"📧 [BACKGROUND] Starting email send for {email}")
                email_sent = send_invitation_async({
                    'name': name,
                    'email': email,
                    'employee_id': employee_id,
                    'role': role
                }, invitation_token)
                
                if email_sent:
                    logger.info(f"✅ [BACKGROUND] Email sent successfully to {email}")
                else:
                    logger.warning(f"⚠️ [BACKGROUND] Email failed for {email}")
            except Exception as e:
                logger.error(f"❌ [BACKGROUND] Email error for {email}: {str(e)}")
        
        # Start background thread for email sending
        email_thread = threading.Thread(target=send_email_background)
        email_thread.daemon = True  # Thread will terminate when main program exits
        email_thread.start()
        
        logger.info(f"📤 Email thread started for {email}")
        
        # Return immediately without waiting for email
        return JsonResponse({
            'success': True,
            'message': f'Employee added successfully! Invitation email is being sent to {email}',
            'employee_id': employee_id,
            'name': name,
            'email_status': 'sending'
        })
        
    except Exception as e:
        logger.error(f"Add employee with invitation error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_resend_invitation(request):
    """API endpoint to resend invitation email"""
    if not request.session.get('user_id'):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        data = json.loads(request.body)
        employee_db_id = data.get('id')
        
        if not employee_db_id:
            return JsonResponse({'error': 'Employee ID is required'}, status=400)
        
        client = get_supabase_client()
        
        # Get employee
        result = client.table('employees')\
            .select('*')\
            .eq('id', employee_db_id)\
            .execute()
        
        if not result.data:
            return JsonResponse({'error': 'Employee not found'}, status=404)
        
        employee = result.data[0]
        
        # Check if already active
        if employee.get('status') == 'active' and employee.get('invitation_accepted_at'):
            return JsonResponse({'error': 'Employee has already accepted invitation'}, status=400)
        
        # Generate new token
        new_token = secrets.token_urlsafe(32)
        
        # Update employee with new token
        client.table('employees')\
            .update({
                'invitation_token': new_token,
                'invitation_sent_at': datetime.now().isoformat()
            })\
            .eq('id', employee_db_id)\
            .execute()
        
        # Resend invitation email
        email_sent = send_employee_invitation({
            'name': employee['name'],
            'email': employee['email'],
            'employee_id': employee['employee_id'],
            'role': employee['role']
        }, new_token)
        
        logger.info(f"Invitation resent to: {employee['email']}")
        
        return JsonResponse({
            'success': True,
            'message': f'Invitation email resent to {employee["email"]}',
            'email_sent': email_sent
        })
        
    except Exception as e:
        logger.error(f"Resend invitation error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
