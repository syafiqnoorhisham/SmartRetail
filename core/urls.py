from django.urls import path
from . import views
from .invitation_views import (
    invitation_accept_view,
    invitation_accept_submit,
    api_add_employee_with_invitation,
    api_resend_invitation
)

urlpatterns = [
    # Auth
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('login/submit/', views.login_submit, name='login_submit'),
    # Signup routes commented out - now invitation-only
    # path('signup/', views.signup_view, name='signup'),
    # path('signup/submit/', views.signup_submit, name='signup_submit'),
    path('logout/', views.logout_view, name='logout'),
    
    # Invitation Flow
    path('invitation/accept/<str:token>/', invitation_accept_view, name='invitation_accept'),
    path('invitation/submit/<str:token>/', invitation_accept_submit, name='invitation_accept_submit'),
    
    # Dashboard pages
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('inventory/', views.inventory_view, name='inventory'),
    path('sales/', views.sales_view, name='sales'),
    path('employees/', views.employees_view, name='employees'),
    path('suppliers/', views.suppliers_view, name='suppliers'),
    path('report/', views.report_view, name='report'),
    
    # API endpoints - Products
    path('api/metrics/', views.api_dashboard_metrics, name='api_dashboard_metrics'),
    path('api/stock/add/', views.api_add_stock, name='api_add_stock'),
    path('api/product/update/', views.api_update_product, name='api_update_product'),
    path('api/product/delete/', views.api_delete_product, name='api_delete_product'),
    
    # API endpoints - Employees
    path('api/employee/add/', api_add_employee_with_invitation, name='api_add_employee'),  # Updated to use invitation
    path('api/employee/update/', views.api_update_employee, name='api_update_employee'),
    path('api/employee/delete/', views.api_delete_employee, name='api_delete_employee'),
    path('api/employee/resend-invitation/', api_resend_invitation, name='api_resend_invitation'),
    
    # API endpoints - Sales
    path('api/sale/create/', views.api_create_sale, name='api_create_sale'),
    path('api/sale/get/', views.api_get_sale, name='api_get_sale'),
    path('api/sale/delete/', views.api_delete_sale, name='api_delete_sale'),
]
