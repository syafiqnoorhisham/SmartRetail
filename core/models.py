"""
Django models for SmartRetail Dashboard
These models mirror the Supabase database schema
"""

from django.db import models
from django.utils import timezone


class Employee(models.Model):
    """Employee model matching Supabase employees table"""
    
    ROLE_CHOICES = [
        ('Sales', 'Sales'),  # Changed from 'User' to 'Sales'
        ('Supplier', 'Supplier'),
        ('Manager', 'Manager'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('on_leave', 'On Leave'),
        ('pending', 'Pending'),  # New status for invited users
    ]
    
    employee_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    position = models.CharField(max_length=100, null=True, blank=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='Sales')
    address = models.TextField(null=True, blank=True)  # New field
    profile_picture = models.TextField(null=True, blank=True)  # New field for image URL/base64
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')  # Default to pending
    invitation_token = models.CharField(max_length=100, null=True, blank=True)  # New field for invitation
    invitation_sent_at = models.DateTimeField(null=True, blank=True)  # New field
    invitation_accepted_at = models.DateTimeField(null=True, blank=True)  # New field
    hire_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'employees'
        managed = False  # Supabase manages this table
        
    def __str__(self):
        return f"{self.employee_id} - {self.name}"


class Product(models.Model):
    """Product model matching Supabase products table"""
    
    STATUS_CHOICES = [
        ('high_stock', 'High Stock'),
        ('completed', 'Completed'),
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
    ]
    
    product_id = models.CharField(max_length=50, unique=True)
    product_code = models.CharField(max_length=50, null=True, blank=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    category_id = models.BigIntegerField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    current_stock = models.IntegerField(default=0)
    max_stock = models.IntegerField(default=50)
    low_stock_threshold = models.IntegerField(default=10)
    unit = models.CharField(max_length=20, default='unit')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_stock')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'products'
        managed = False
        
    def __str__(self):
        return f"{self.product_id} - {self.name}"
    
    @property
    def stock_display(self):
        """Return stock in format: 38/50"""
        return f"{self.current_stock}/{self.max_stock}"
    
    @property
    def is_low_stock(self):
        """Check if product is low on stock"""
        return self.current_stock <= self.low_stock_threshold
    
    @property
    def stock_percentage(self):
        """Calculate stock percentage"""
        if self.max_stock > 0:
            return (self.current_stock / self.max_stock) * 100
        return 0


class Sale(models.Model):
    """Sales transaction model matching Supabase sales table"""
    
    PAYMENT_METHODS = [
        ('CARD', 'Card'),
        ('CASH', 'Cash'),
        ('EWALLET', 'E-Wallet'),
        ('Ewallet', 'E-wallet'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    sale_id = models.CharField(max_length=50, unique=True)
    user_id = models.CharField(max_length=50)
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    sales_date = models.DateTimeField(default=timezone.now)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'sales'
        managed = False
        ordering = ['-sales_date']
        
    def __str__(self):
        return f"{self.sale_id} - RM{self.total_amount}"


class SaleItem(models.Model):
    """Sale line items matching Supabase sales_items table"""
    
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'sales_items'
        managed = False
        
    def __str__(self):
        return f"{self.sale.sale_id} - {self.product.name if self.product else 'N/A'}"
