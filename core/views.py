from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import base64
import re
from django.core.serializers.json import DjangoJSONEncoder
from .supabase_client import get_supabase_client
from .utils.supabase_queries import (
    get_dashboard_metrics,
    get_products_by_category,
    get_all_categories,
    search_products
)
from .utils.report_queries import (
    get_best_selling_products,
    get_best_selling_categories,
    get_low_stock_products,
    get_total_sales,
    get_profit_revenue_trend,
    get_report_date,
    get_report_metadata
)
import logging

logger = logging.getLogger(__name__)


def calculate_stock_status(current_stock, max_stock, low_stock_threshold):
    """
    Calculate product status based on stock levels
    
    Returns:
        - 'out_of_stock': current_stock == 0
        - 'low_stock': current_stock <= low_stock_threshold
        - 'high_stock': current_stock >= max_stock
        - 'completed': normal stock levels
    """
    if current_stock == 0:
        return 'out_of_stock'
    elif current_stock <= low_stock_threshold:
        return 'low_stock'
    elif current_stock >= max_stock:
        return 'high_stock'
    else:
        return 'completed'


def login_view(request):
    """Display login page and handle login requests"""
    # If user is already logged in, redirect to dashboard
    if request.session.get('user_id'):
        return redirect('dashboard')
    
    return render(request, 'login.html')


@require_http_methods(["POST"])
def login_submit(request):
    """Handle login form submission with Supabase authentication"""
    email = request.POST.get('email', '').strip()
    password = request.POST.get('password', '')
    
    # Validation
    if not email or not password:
        messages.error(request, 'Email and password are required.')
        return redirect('login')
    
    try:
        # Initialize Supabase client
        supabase = get_supabase_client()
        
        # Log the attempt (without password)
        logger.info(f"Login attempt for email: {email}")
        
        # Attempt to sign in with Supabase
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        # Log response for debugging
        logger.info(f"Supabase response received for: {email}")
        
        # Check if authentication was successful
        if response.user:
            # Store user information in session
            request.session['user_id'] = response.user.id
            request.session['user_email'] = response.user.email
            request.session['access_token'] = response.session.access_token
            
            logger.info(f"Login successful for user: {email}")
            messages.success(request, 'Login successful!')
            return redirect('dashboard')
        else:
            logger.warning(f"Login failed for {email}: No user in response")
            messages.error(request, 'Invalid email or password.')
            return redirect('login')
            
    except Exception as e:
        # Log the full error for debugging
        logger.error(f"Login error for {email}: {type(e).__name__} - {str(e)}")
        
        # Check for specific error messages
        error_message = str(e).lower()
        
        if 'invalid login credentials' in error_message or 'invalid' in error_message:
            messages.error(request, 'Invalid email or password. Please check your credentials.')
        elif 'email not confirmed' in error_message:
            messages.error(request, 'Please confirm your email before logging in.')
        elif 'network' in error_message or 'connection' in error_message:
            messages.error(request, 'Network error. Please check your internet connection.')
        else:
            messages.error(request, f'Login failed: {str(e)}')
        
        return redirect('login')


def logout_view(request):
    """Handle user logout"""
    try:
        # Clear session
        request.session.flush()
        messages.success(request, 'You have been logged out successfully.')
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
    
    return redirect('login')


def signup_view(request):
    """Display signup page with role selection"""
    # If user is already logged in, redirect to dashboard
    if request.session.get('user_id'):
        return redirect('dashboard')
    
    # Get selected role from query parameter (from role selection page)
    selected_role = request.GET.get('role', None)
    
    return render(request, 'signup.html', {'selected_role': selected_role})


@require_http_methods(["POST"])
def signup_submit(request):
    """Handle signup form submission"""
    name = request.POST.get('name', '').strip()
    email = request.POST.get('email', '').strip()
    password = request.POST.get('password', '')
    re_password = request.POST.get('re_password', '')
    role = request.POST.get('role', 'Sales')  # Changed default from 'User' to 'Sales'
    
    # Validation
    if not all([name, email, password, re_password]):
        messages.error(request, 'All fields are required.')
        return redirect(f'/signup/?role={role}')
    
    if password != re_password:
        messages.error(request, 'Passwords do not match.')
        return redirect(f'/signup/?role={role}')
    
    if len(password) < 6:
        messages.error(request, 'Password must be at least 6 characters long.')
        return redirect(f'/signup/?role={role}')
    
    try:
        # Initialize Supabase client
        supabase = get_supabase_client()
        
        logger.info(f"Signup attempt for email: {email}")
        
        # Create user in Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "name": name,
                    "role": role
                }
            }
        })
        
        if auth_response.user:
            # Generate employee ID
            role_prefixes = {
                'Sales': 'S',  # Changed from 'User' to 'Sales'
                'Supplier': 'SP',
                'Manager': 'M'
            }
            prefix = role_prefixes.get(role, 'S')
            
            # Get existing employees to find next ID
            employees_result = supabase.table('employees')\
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
            
            # Create employee record
            employee_data = {
                'employee_id': employee_id,
                'name': name,
                'email': email,
                'role': role,
                'status': 'active'
            }
            
            supabase.table('employees').insert(employee_data).execute()
            
            logger.info(f"Signup successful for: {email}")
            messages.success(request, 'Account created successfully! Please check your email to verify your account, then login.')
            return redirect('login')
        else:
            logger.warning(f"Signup failed for {email}: No user in response")
            messages.error(request, 'Signup failed. Please try again.')
            return redirect(f'/signup/?role={role}')
            
    except Exception as e:
        logger.error(f"Signup error for {email}: {type(e).__name__} - {str(e)}")
        
        error_message = str(e).lower()
        
        if 'already registered' in error_message or 'already exists' in error_message:
            messages.error(request, 'This email is already registered. Please login instead.')
        elif 'invalid email' in error_message:
            messages.error(request, 'Please enter a valid email address.')
        else:
            messages.error(request, f'Signup failed: {str(e)}')
        
        return redirect(f'/signup/?role={role}')


def dashboard_view(request):
    """Display main dashboard with metrics"""
    # Check if user is authenticated
    if not request.session.get('user_id'):
        messages.warning(request, 'Please login to access the dashboard.')
        return redirect('login')
    
    try:
        # Get all dashboard metrics
        metrics = get_dashboard_metrics()
        
        context = {
            'user_email': request.session.get('user_email', 'User'),
            'sales_data': metrics['sales'],
            'items_data': metrics['items'],
            'employee_data': metrics['employees'],
            'low_stock_products': metrics['low_stock'],
            'recent_transactions': metrics['recent_transactions'],
            'sales_trend': metrics['sales_trend'],
        }
        
        return render(request, 'dashboard/index.html', context)
        
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        messages.error(request, 'Error loading dashboard data.')
        
        # Return with empty context
        context = {
            'user_email': request.session.get('user_email', 'User'),
            'sales_data': {'today': 0, 'percentage': 0, 'is_positive': True},
            'items_data': {'today': 0, 'percentage': 0, 'is_positive': True},
            'employee_data': {'active': 0, 'total': 0},
            'low_stock_products': [],
            'recent_transactions': [],
            'sales_trend': [],
        }
        
        return render(request, 'dashboard/index.html', context)


def inventory_view(request):
    """Display inventory page with category filtering and search"""
    # Check if user is authenticated
    if not request.session.get('user_id'):
        messages.warning(request, 'Please login to access the inventory.')
        return redirect('login')
    
    try:
        # Get parameters from query string
        selected_category = request.GET.get('category', None)
        search_query = request.GET.get('search', '').strip()
        
        # Get all categories
        categories = get_all_categories()
        
        # Get products based on category and search
        if search_query:
            # If searching, filter by category if one is selected
            if selected_category:
                # Category-specific search
                all_products_in_category = get_products_by_category(selected_category)
                products = [
                    p for p in all_products_in_category
                    if search_query.lower() in p['name'].lower() or 
                       search_query.lower() in p['product_id'].lower()
                ]
            else:
                # Global search (All tab)
                products = search_products(search_query)
        elif selected_category:
            # Show products in selected category
            products = get_products_by_category(selected_category)
        else:
            # Default: Show all products (All tab)
            products = get_products_by_category()
        
        # Get all products for the modal dropdown
        all_products = get_products_by_category()
        
        # Count products by category for display
        product_counts = {}
        for category in categories:
            product_counts[category] = len(get_products_by_category(category))
        
        context = {
            'user_email': request.session.get('user_email', 'User'),
            'categories': categories,
            'selected_category': selected_category,
            'products': products,
            'all_products': all_products,
            'search_query': search_query,
            'product_counts': product_counts,
            'total_products': len(all_products),
        }
        
        return render(request, 'dashboard/inventory.html', context)
        
    except Exception as e:
        logger.error(f"Inventory error: {str(e)}")
        messages.error(request, 'Error loading inventory data.')
        return redirect('dashboard')


def sales_view(request):
    """Display sales page with list of sales and POS interface"""
    if not request.session.get('user_id'):
        messages.warning(request, 'Please login to access sales.')
        return redirect('login')
    
    try:
        supabase = get_supabase_client()
        
        # Get all sales with items
        sales_result = supabase.table('sales')\
            .select('*')\
            .order('sales_date', desc=True)\
            .execute()
        
        sales = sales_result.data if sales_result.data else []
        
        # Get all products for POS
        products_result = supabase.table('products')\
            .select('*')\
            .order('category, name')\
            .execute()
        
        products = products_result.data if products_result.data else []
        
        # Get unique categories
        categories = list(set([p['category'] for p in products]))
        categories.sort()
        
        context = {
            'user_email': request.session.get('user_email', 'User'),
            'sales': sales,
            'products': products,
            'categories': categories,
        }
        
        return render(request, 'dashboard/sales.html', context)
        
    except Exception as e:
        logger.error(f"Sales view error: {str(e)}")
        messages.error(request, 'Error loading sales data.')
        
        context = {
            'user_email': request.session.get('user_email', 'User'),
            'sales': [],
            'products': [],
            'categories': [],
        }
        
        return render(request, 'dashboard/sales.html', context)


def employees_view(request):
    """Display employees page with role filtering and search"""
    if not request.session.get('user_id'):
        messages.warning(request, 'Please login to access employees.')
        return redirect('login')
    
    try:
        supabase = get_supabase_client()
        
        # Get parameters from query string
        selected_role = request.GET.get('role', None)
        search_query = request.GET.get('search', '').strip()
        
        # Build query
        query = supabase.table('employees').select('*')
        
        # Filter by role if specified
        if selected_role:
            query = query.eq('role', selected_role)
        
        # Execute query
        result = query.execute()
        employees = result.data if result.data else []
        
        # Apply search filter if provided
        if search_query:
            search_lower = search_query.lower()
            employees = [
                emp for emp in employees
                if search_lower in emp.get('name', '').lower() or
                   search_lower in emp.get('email', '').lower() or
                   search_lower in emp.get('employee_id', '').lower()
            ]
        
        # Count employees by role
        all_employees = supabase.table('employees').select('role').execute()
        role_counts = {'Manager': 0, 'Supplier': 0, 'Sales': 0}
        for emp in all_employees.data if all_employees.data else []:
            role = emp.get('role', '')
            if role in role_counts:
                role_counts[role] += 1
        
        context = {
            'user_email': request.session.get('user_email', 'User'),
            'employees': employees,
            'selected_role': selected_role,
            'search_query': search_query,
            'total_employees': len(all_employees.data) if all_employees.data else 0,
            'role_counts': role_counts,
        }
        
        return render(request, 'dashboard/employees.html', context)
        
    except Exception as e:
        logger.error(f"Employees view error: {str(e)}")
        messages.error(request, 'Error loading employees data.')
        return redirect('dashboard')


def suppliers_view(request):
    """Display suppliers page"""
    if not request.session.get('user_id'):
        messages.warning(request, 'Please login to access suppliers.')
        return redirect('login')
    
    context = {
        'user_email': request.session.get('user_email', 'User'),
    }
    
    return render(request, 'dashboard/suppliers.html', context)


def report_view(request):
    """Display report page with analytics"""
    if not request.session.get('user_id'):
        messages.warning(request, 'Please login to access reports.')
        return redirect('login')
    
    try:
        # Get all report data
        best_products = get_best_selling_products(limit=10)
        best_categories = get_best_selling_categories(limit=3)
        low_stock = get_low_stock_products(limit=3)
        
        # Get total sales for different periods
        total_today = get_total_sales('today')
        total_week = get_total_sales('week')
        total_month = get_total_sales('month')
        
        # Get chart data
        chart_data = get_profit_revenue_trend(months=7)
        
        # Get report metadata
        report_date = get_report_date()
        report_metadata = get_report_metadata()
        
        # Serialize chart data as JSON for template
        chart_data_json = json.dumps(chart_data, cls=DjangoJSONEncoder)
        
        context = {
            'user_email': request.session.get('user_email', 'User'),
            'best_products': best_products,
            'best_categories': best_categories,
            'low_stock': low_stock,
            'total_today': total_today,
            'total_week': total_week,
            'total_month': total_month,
            'chart_data': chart_data,
            'chart_data_json': chart_data_json,
            'report_date': report_date,
            'report_metadata': report_metadata,
        }
        
        return render(request, 'dashboard/report.html', context)
        
    except Exception as e:
        logger.error(f"Report view error: {str(e)}")
        messages.error(request, 'Error loading report data.')
        
        # Return with empty context
        context = {
            'user_email': request.session.get('user_email', 'User'),
            'best_products': [],
            'best_categories': [],
            'low_stock': [],
            'total_today': 'RM0.00',
            'total_week': 'RM0.00',
            'total_month': 'RM0.00',
            'chart_data': {'labels': [], 'revenue': [], 'profit': []},
            'report_date': get_report_date(),
            'report_metadata': get_report_metadata(),
        }
        
        return render(request, 'dashboard/report.html', context)


def report_print_view(request):
    """Display printable report page"""
    if not request.session.get('user_id'):
        messages.warning(request, 'Please login to access reports.')
        return redirect('login')
    
    try:
        # Get all report data (same as regular report view)
        best_products = get_best_selling_products(limit=10)
        best_categories = get_best_selling_categories(limit=3)
        
        # Get total sales for different periods
        total_today = get_total_sales('today')
        total_week = get_total_sales('week')
        total_month = get_total_sales('month')
        
        # Get chart data
        chart_data = get_profit_revenue_trend(months=7)
        
        # Get report metadata
        report_metadata = get_report_metadata()
        
        # Serialize chart data as JSON for template
        chart_data_json = json.dumps(chart_data, cls=DjangoJSONEncoder)
        
        context = {
            'best_products': best_products,
            'best_categories': best_categories,
            'total_today': total_today,
            'total_week': total_week,
            'total_month': total_month,
            'chart_data': chart_data,
            'chart_data_json': chart_data_json,
            'report_metadata': report_metadata,
        }
        
        return render(request, 'dashboard/report_print.html', context)
        
    except Exception as e:
        logger.error(f"Report print view error: {str(e)}")
        
        # Return with empty context
        context = {
            'best_products': [],
            'best_categories': [],
            'total_today': 'RM0.00',
            'total_week': 'RM0.00',
            'total_month': 'RM0.00',
            'chart_data': {'labels': [], 'revenue': [], 'profit': []},
            'report_metadata': get_report_metadata(),
        }
        
        return render(request, 'dashboard/report_print.html', context)


# API Endpoints for AJAX requests
def api_dashboard_metrics(request):
    """API endpoint to get dashboard metrics"""
    if not request.session.get('user_id'):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        metrics = get_dashboard_metrics()
        return JsonResponse(metrics)
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_add_stock(request):
    """API endpoint to add stock to a product or create new product"""
    if not request.session.get('user_id'):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        data = json.loads(request.body)
        is_new = data.get('is_new', False)
        quantity = int(data.get('quantity', 0))
        
        if quantity <= 0:
            return JsonResponse({'error': 'Invalid quantity'}, status=400)
        
        client = get_supabase_client()
        
        if is_new:
            # Create new product
            product_name = data.get('product_name', '').strip()
            category = data.get('category', '').strip()
            
            if not product_name or not category:
                return JsonResponse({'error': 'Product name and category are required'}, status=400)
            
            # Generate new product ID
            # Get the highest product ID for the category
            category_prefixes = {
                'Beverages': '1',
                'Bakery & Snacks': '2',
                'Health & Medicine': '3',
                'Stationery': '4',
                'Personal Care & Hygiene': '5'
            }
            
            prefix = category_prefixes.get(category, '9')
            
            # Get existing products in category
            result = client.table('products')\
                .select('product_id')\
                .like('product_id', f'#{prefix}%')\
                .execute()
            
            # Find next available ID
            existing_ids = [p['product_id'] for p in result.data]
            next_num = 0
            for i in range(1000):
                test_id = f"#{prefix}{i:03d}"
                if test_id not in existing_ids:
                    next_num = i
                    break
            
            new_product_id = f"#{prefix}{next_num:03d}"
            
            # Calculate initial status
            max_stock = 50  # Default
            low_stock_threshold = 10  # Default
            initial_status = calculate_stock_status(quantity, max_stock, low_stock_threshold)
            
            # Create the product
            new_product = {
                'product_id': new_product_id,
                'name': product_name,
                'category': category,
                'current_stock': quantity,
                'max_stock': max_stock,
                'low_stock_threshold': low_stock_threshold,
                'price': 0.00,  # Default, can be updated later
                'status': initial_status
            }
            
            insert_result = client.table('products')\
                .insert(new_product)\
                .execute()
            
            return JsonResponse({
                'success': True,
                'message': 'New product created successfully',
                'product_id': new_product_id,
                'new_stock': quantity
            })
            
        else:
            # Add stock to existing product
            product_id = data.get('product_id')
            
            if not product_id:
                return JsonResponse({'error': 'Product ID is required'}, status=400)
            
            # Get current product
            result = client.table('products')\
                .select('*')\
                .eq('product_id', product_id)\
                .execute()
            
            if not result.data:
                return JsonResponse({'error': 'Product not found'}, status=404)
            
            product = result.data[0]
            new_stock = product['current_stock'] + quantity
            
            # Calculate new status based on updated stock
            new_status = calculate_stock_status(
                new_stock,
                product['max_stock'],
                product['low_stock_threshold']
            )
            
            # Update stock and status
            update_result = client.table('products')\
                .update({
                    'current_stock': new_stock,
                    'status': new_status
                })\
                .eq('product_id', product_id)\
                .execute()
            
            return JsonResponse({
                'success': True,
                'message': 'Stock updated successfully',
                'new_stock': new_stock
            })
        
    except Exception as e:
        logger.error(f"Add stock error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_update_product(request):
    """API endpoint to update product details"""
    if not request.session.get('user_id'):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        
        if not product_id:
            return JsonResponse({'error': 'Product ID is required'}, status=400)
        
        client = get_supabase_client()
        
        # Prepare update data
        update_data = {}
        
        if 'product_name' in data:
            update_data['name'] = data['product_name'].strip()
        
        if 'category' in data:
            update_data['category'] = data['category'].strip()
        
        if 'price' in data:
            update_data['price'] = float(data['price'])
        
        if 'current_stock' in data:
            update_data['current_stock'] = int(data['current_stock'])
        
        if 'max_stock' in data:
            update_data['max_stock'] = int(data['max_stock'])
        
        if 'low_stock_threshold' in data:
            update_data['low_stock_threshold'] = int(data['low_stock_threshold'])
        
        if not update_data:
            return JsonResponse({'error': 'No data to update'}, status=400)
        
        # If stock-related fields are being updated, recalculate status
        if any(key in update_data for key in ['current_stock', 'max_stock', 'low_stock_threshold']):
            # Get current product data to fill in missing values
            current_result = client.table('products')\
                .select('current_stock, max_stock, low_stock_threshold')\
                .eq('product_id', product_id)\
                .execute()
            
            if current_result.data:
                current_product = current_result.data[0]
                
                # Use updated values or fall back to current values
                final_current_stock = update_data.get('current_stock', current_product['current_stock'])
                final_max_stock = update_data.get('max_stock', current_product['max_stock'])
                final_low_stock_threshold = update_data.get('low_stock_threshold', current_product['low_stock_threshold'])
                
                # Calculate and set new status
                update_data['status'] = calculate_stock_status(
                    final_current_stock,
                    final_max_stock,
                    final_low_stock_threshold
                )
        
        # Update the product
        result = client.table('products')\
            .update(update_data)\
            .eq('product_id', product_id)\
            .execute()
        
        if not result.data:
            return JsonResponse({'error': 'Product not found'}, status=404)
        
        return JsonResponse({
            'success': True,
            'message': 'Product updated successfully',
            'product': result.data[0]
        })
        
    except Exception as e:
        logger.error(f"Update product error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_delete_product(request):
    """API endpoint to delete a product"""
    if not request.session.get('user_id'):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        
        if not product_id:
            return JsonResponse({'error': 'Product ID is required'}, status=400)
        
        client = get_supabase_client()
        
        # Check if product exists first
        check_result = client.table('products')\
            .select('product_id, name')\
            .eq('product_id', product_id)\
            .execute()
        
        if not check_result.data:
            return JsonResponse({'error': 'Product not found'}, status=404)
        
        product_name = check_result.data[0]['name']
        
        # Delete the product
        delete_result = client.table('products')\
            .delete()\
            .eq('product_id', product_id)\
            .execute()
        
        logger.info(f"Product deleted: {product_id} - {product_name}")
        
        return JsonResponse({
            'success': True,
            'message': f'Product {product_name} deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Delete product error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


# Employee Management API Endpoints

@csrf_exempt
@require_http_methods(["POST"])
def api_add_employee(request):
    """API endpoint to add a new employee"""
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
        
        # Create employee record
        employee_data = {
            'employee_id': employee_id,
            'name': name,
            'email': email,
            'role': role,
            'address': address if address else None,
            'profile_picture': profile_picture,
            'status': 'active'
        }
        
        result = client.table('employees').insert(employee_data).execute()
        
        logger.info(f"Employee added: {employee_id} - {name}")
        
        return JsonResponse({
            'success': True,
            'message': 'Employee added successfully',
            'employee_id': employee_id,
            'name': name
        })
        
    except Exception as e:
        logger.error(f"Add employee error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_update_employee(request):
    """API endpoint to update employee details"""
    if not request.session.get('user_id'):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        # Get form data
        employee_db_id = request.POST.get('id', '').strip()
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        role = request.POST.get('role', '').strip()
        address = request.POST.get('address', '').strip()
        current_profile = request.POST.get('current_profile_picture', '')
        
        # Validation
        if not employee_db_id:
            return JsonResponse({'error': 'Employee ID is required'}, status=400)
        
        if not name or not email or not role:
            return JsonResponse({'error': 'Name, email, and role are required'}, status=400)
        
        # Validate email format
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_regex, email):
            return JsonResponse({'error': 'Invalid email format'}, status=400)
        
        if role not in ['Manager', 'Supplier', 'Sales']:
            return JsonResponse({'error': 'Invalid role'}, status=400)
        
        client = get_supabase_client()
        
        # Check for duplicate email (excluding current employee)
        email_check = client.table('employees')\
            .select('id, email')\
            .eq('email', email)\
            .execute()
        
        if email_check.data:
            for emp in email_check.data:
                if str(emp['id']) != employee_db_id:
                    return JsonResponse({'error': 'Email already exists'}, status=400)
        
        # Prepare update data
        update_data = {
            'name': name,
            'email': email,
            'role': role,
            'address': address if address else None
        }
        
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            file = request.FILES['profile_picture']
            
            # Validate file size (2MB)
            if file.size > 2 * 1024 * 1024:
                return JsonResponse({'error': 'Profile picture must be less than 2MB'}, status=400)
            
            # Convert to base64
            file_content = file.read()
            update_data['profile_picture'] = f"data:{file.content_type};base64,{base64.b64encode(file_content).decode('utf-8')}"
        elif current_profile:
            # Keep existing profile picture
            update_data['profile_picture'] = current_profile
        else:
            # Remove profile picture
            update_data['profile_picture'] = None
        
        # Update the employee
        result = client.table('employees')\
            .update(update_data)\
            .eq('id', employee_db_id)\
            .execute()
        
        if not result.data:
            return JsonResponse({'error': 'Employee not found'}, status=404)
        
        logger.info(f"Employee updated: {name}")
        
        return JsonResponse({
            'success': True,
            'message': 'Employee updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Update employee error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_delete_employee(request):
    """API endpoint to delete an employee"""
    if not request.session.get('user_id'):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        data = json.loads(request.body)
        employee_db_id = data.get('id')
        
        if not employee_db_id:
            return JsonResponse({'error': 'Employee ID is required'}, status=400)
        
        client = get_supabase_client()
        
        # Check if employee exists first
        check_result = client.table('employees')\
            .select('id, employee_id, name')\
            .eq('id', employee_db_id)\
            .execute()
        
        if not check_result.data:
            return JsonResponse({'error': 'Employee not found'}, status=404)
        
        employee = check_result.data[0]
        employee_id = employee['employee_id']
        employee_name = employee['name']
        
        # Delete the employee
        delete_result = client.table('employees')\
            .delete()\
            .eq('id', employee_db_id)\
            .execute()
        
        logger.info(f"Employee deleted: {employee_id} - {employee_name}")
        
        return JsonResponse({
            'success': True,
            'message': f'Employee {employee_name} deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Delete employee error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


# Sales API Endpoints

@csrf_exempt
@require_http_methods(["POST"])
def api_create_sale(request):
    """API endpoint to create a new sale transaction"""
    if not request.session.get('user_id'):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        data = json.loads(request.body)
        payment_method = data.get('payment_method')
        total_amount = float(data.get('total_amount', 0))
        items = data.get('items', [])
        
        if not payment_method or total_amount <= 0 or not items:
            return JsonResponse({'error': 'Invalid sale data'}, status=400)
        
        client = get_supabase_client()
        user_id = request.session.get('user_id')
        
        # Generate sale ID
        sales_result = client.table('sales')\
            .select('sale_id')\
            .execute()
        
        existing_ids = [s['sale_id'] for s in sales_result.data] if sales_result.data else []
        next_num = 1
        for i in range(1, 100000):
            test_id = f"{i:04d}"
            if test_id not in existing_ids:
                next_num = i
                break
        
        sale_id = f"{next_num:04d}"
        
        # Create sale record
        from datetime import datetime
        sale_data = {
            'sale_id': sale_id,
            'user_id': f"#{user_id[:3]}" if len(user_id) > 3 else f"#{user_id}",
            'total_amount': total_amount,
            'payment_method': payment_method,
            'status': 'completed',
            'sales_date': datetime.now().isoformat()
        }
        
        sale_result = client.table('sales').insert(sale_data).execute()
        
        if not sale_result.data:
            return JsonResponse({'error': 'Failed to create sale'}, status=500)
        
        sale = sale_result.data[0]
        
        # Create sale items and update product stock
        sale_items = []
        for item in items:
            product_id = item['product_id']
            quantity = item['quantity']
            
            # Get product details
            product_result = client.table('products')\
                .select('*')\
                .eq('product_id', product_id)\
                .execute()
            
            if product_result.data:
                product = product_result.data[0]
                
                # Create sale item
                sale_item = {
                    'sale_id': sale['id'],
                    'product_id': product['id'],
                    'quantity': quantity,
                    'unit_price': item['unit_price'],
                    'subtotal': item['subtotal']
                }
                
                item_result = client.table('sales_items').insert(sale_item).execute()
                
                if item_result.data:
                    sale_items.append({
                        'product_name': product['name'],
                        'quantity': quantity,
                        'subtotal': item['subtotal']
                    })
                
                # Update product stock
                new_stock = max(0, product['current_stock'] - quantity)
                new_status = calculate_stock_status(
                    new_stock,
                    product['max_stock'],
                    product['low_stock_threshold']
                )
                
                client.table('products')\
                    .update({
                        'current_stock': new_stock,
                        'status': new_status
                    })\
                    .eq('product_id', product_id)\
                    .execute()
        
        logger.info(f"Sale created: {sale_id} - RM{total_amount}")
        
        return JsonResponse({
            'success': True,
            'message': 'Sale created successfully',
            'sale': {
                'id': sale['id'],
                'sale_id': sale['sale_id'],
                'user_id': sale['user_id'],
                'total_amount': sale['total_amount'],
                'payment_method': sale['payment_method'],
                'sales_date': sale['sales_date'],
                'items': sale_items
            }
        })
        
    except Exception as e:
        logger.error(f"Create sale error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_delete_sale(request):
    """API endpoint to delete a sale transaction"""
    if not request.session.get('user_id'):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        data = json.loads(request.body)
        sale_db_id = data.get('id')
        
        if not sale_db_id:
            return JsonResponse({'error': 'Sale ID is required'}, status=400)
        
        client = get_supabase_client()
        
        # Check if sale exists and get items
        sale_result = client.table('sales')\
            .select('id, sale_id, total_amount')\
            .eq('id', sale_db_id)\
            .execute()
        
        if not sale_result.data:
            return JsonResponse({'error': 'Sale not found'}, status=404)
        
        sale = sale_result.data[0]
        sale_id = sale['sale_id']
        
        # Get sale items to restore stock
        items_result = client.table('sales_items')\
            .select('*, products(*)')\
            .eq('sale_id', sale_db_id)\
            .execute()
        
        # Restore product stock
        if items_result.data:
            for item in items_result.data:
                if item.get('products'):
                    product = item['products']
                    product_id = product['product_id']
                    quantity = item['quantity']
                    
                    # Restore stock
                    new_stock = product['current_stock'] + quantity
                    new_status = calculate_stock_status(
                        new_stock,
                        product['max_stock'],
                        product['low_stock_threshold']
                    )
                    
                    client.table('products')\
                        .update({
                            'current_stock': new_stock,
                            'status': new_status
                        })\
                        .eq('product_id', product_id)\
                        .execute()
        
        # Delete sale items first
        client.table('sales_items')\
            .delete()\
            .eq('sale_id', sale_db_id)\
            .execute()
        
        # Delete the sale
        client.table('sales')\
            .delete()\
            .eq('id', sale_db_id)\
            .execute()
        
        logger.info(f"Sale deleted: {sale_id}")
        
        return JsonResponse({
            'success': True,
            'message': f'Sale {sale_id} deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Delete sale error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def api_get_sale(request):
    """API endpoint to get sale details for receipt viewing"""
    if not request.session.get('user_id'):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        sale_id = request.GET.get('id')
        
        if not sale_id:
            return JsonResponse({'error': 'Sale ID is required'}, status=400)
        
        client = get_supabase_client()
        
        # Get sale details
        sale_result = client.table('sales')\
            .select('*')\
            .eq('id', sale_id)\
            .execute()
        
        if not sale_result.data:
            return JsonResponse({'error': 'Sale not found'}, status=404)
        
        sale = sale_result.data[0]
        
        # Get sale items with product details
        items_result = client.table('sales_items')\
            .select('*, products(name)')\
            .eq('sale_id', sale_id)\
            .execute()
        
        # Format items for receipt
        sale_items = []
        if items_result.data:
            for item in items_result.data:
                sale_items.append({
                    'product_name': item['products']['name'] if item.get('products') else 'Unknown Product',
                    'quantity': item['quantity'],
                    'subtotal': float(item['subtotal'])
                })
        
        return JsonResponse({
            'success': True,
            'sale': {
                'id': sale['id'],
                'sale_id': sale['sale_id'],
                'user_id': sale['user_id'],
                'total_amount': float(sale['total_amount']),
                'payment_method': sale['payment_method'],
                'sales_date': sale['sales_date'],
                'items': sale_items
            }
        })
        
    except Exception as e:
        logger.error(f"Get sale error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
