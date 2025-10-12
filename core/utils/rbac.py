"""
Role-based access control utilities for SmartRetail
Handles permission checks and access restrictions based on user roles
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from ..supabase_client import get_supabase_client
import logging

logger = logging.getLogger(__name__)


def get_user_role(request):
    """
    Get the role of the currently logged-in user
    
    Returns:
        str: User role ('Manager', 'Sales', or None)
    """
    if not request.session.get('user_id'):
        return None
    
    try:
        user_email = request.session.get('user_email')
        if not user_email:
            return None
        
        client = get_supabase_client()
        result = client.table('employees')\
            .select('role')\
            .eq('email', user_email)\
            .execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]['role']
        
        return None
    except Exception as e:
        logger.error(f"Error getting user role: {str(e)}")
        return None


def require_role(allowed_roles):
    """
    Decorator to restrict access to views based on user role
    
    Args:
        allowed_roles (list): List of roles that can access the view
    
    Usage:
        @require_role(['Manager'])
        def admin_only_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Check if user is authenticated
            if not request.session.get('user_id'):
                messages.warning(request, 'Please login to access this page.')
                return redirect('login')
            
            # Get user role
            user_role = get_user_role(request)
            
            if user_role is None:
                messages.error(request, 'Unable to determine your role. Please contact administrator.')
                return redirect('dashboard')
            
            # Check if user has required role
            if user_role not in allowed_roles:
                messages.error(request, f'Access denied. This page is restricted to {", ".join(allowed_roles)} only.')
                return redirect('dashboard')
            
            # Store role in request for use in view
            request.user_role = user_role
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def check_permission(request, permission):
    """
    Check if user has a specific permission
    
    Args:
        request: Django request object
        permission (str): Permission to check
            - 'view_employees'
            - 'manage_employees'
            - 'view_reports'
            - 'manage_inventory'
            - 'view_inventory'
            - 'manage_sales'
            - 'view_sales'
    
    Returns:
        bool: True if user has permission, False otherwise
    """
    user_role = get_user_role(request)
    
    if user_role is None:
        return False
    
    # Manager has all permissions
    if user_role == 'Manager':
        return True
    
    # Sales role permissions
    if user_role == 'Sales':
        sales_permissions = [
            'view_inventory',  # View-only access to inventory
            'manage_sales',    # Full access to sales
            'view_sales',      # Can view sales
        ]
        return permission in sales_permissions
    
    return False


def get_role_permissions(role):
    """
    Get all permissions for a specific role
    
    Args:
        role (str): User role
    
    Returns:
        dict: Dictionary of permissions
    """
    if role == 'Manager':
        return {
            'view_dashboard': True,
            'view_employee_stats': True,
            'view_sales': True,
            'manage_sales': True,
            'view_inventory': True,
            'manage_inventory': True,
            'view_employees': True,
            'manage_employees': True,
            'view_reports': True,
        }
    elif role == 'Sales':
        return {
            'view_dashboard': True,
            'view_employee_stats': False,  # Cannot see employee stats
            'view_sales': True,
            'manage_sales': True,          # Full access to sales
            'view_inventory': True,        # View-only
            'manage_inventory': False,     # Cannot add/edit/delete products
            'view_employees': False,       # No access
            'manage_employees': False,     # No access
            'view_reports': False,         # No access
        }
    else:
        # Default: no permissions
        return {
            'view_dashboard': False,
            'view_employee_stats': False,
            'view_sales': False,
            'manage_sales': False,
            'view_inventory': False,
            'manage_inventory': False,
            'view_employees': False,
            'manage_employees': False,
            'view_reports': False,
        }


def add_permissions_to_context(request, context):
    """
    Add user role and permissions to template context
    
    Args:
        request: Django request object
        context (dict): Template context dictionary
    
    Returns:
        dict: Updated context with role and permissions
    """
    user_role = get_user_role(request)
    permissions = get_role_permissions(user_role) if user_role else {}
    
    context['user_role'] = user_role
    context['permissions'] = permissions
    
    return context
