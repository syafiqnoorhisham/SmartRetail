"""
Supabase Query Utilities for SmartRetail Dashboard
These functions handle all database queries using Supabase client
"""

from datetime import datetime, timedelta
from decimal import Decimal
from core.supabase_client import get_supabase_client


def get_today_sales():
    """Get today's total sales amount"""
    try:
        client = get_supabase_client()
        today = datetime.now().date()
        
        result = client.table('sales')\
            .select('total_amount')\
            .gte('sales_date', f'{today}T00:00:00')\
            .lte('sales_date', f'{today}T23:59:59')\
            .eq('status', 'completed')\
            .execute()
        
        if result.data:
            total = sum(float(item['total_amount']) for item in result.data)
            return Decimal(str(total))
        return Decimal('0.00')
    except Exception as e:
        print(f"Error getting today's sales: {e}")
        return Decimal('0.00')


def get_yesterday_sales():
    """Get yesterday's total sales amount"""
    try:
        client = get_supabase_client()
        yesterday = (datetime.now() - timedelta(days=1)).date()
        
        result = client.table('sales')\
            .select('total_amount')\
            .gte('sales_date', f'{yesterday}T00:00:00')\
            .lte('sales_date', f'{yesterday}T23:59:59')\
            .eq('status', 'completed')\
            .execute()
        
        if result.data:
            total = sum(float(item['total_amount']) for item in result.data)
            return Decimal(str(total))
        return Decimal('0.00')
    except Exception as e:
        print(f"Error getting yesterday's sales: {e}")
        return Decimal('0.00')


def get_sales_comparison():
    """Get sales comparison between today and yesterday"""
    today_sales = get_today_sales()
    yesterday_sales = get_yesterday_sales()
    
    if yesterday_sales > 0:
        change = ((today_sales - yesterday_sales) / yesterday_sales) * 100
        return {
            'today': float(today_sales),
            'yesterday': float(yesterday_sales),
            'percentage': round(float(change), 1),
            'is_positive': change >= 0
        }
    
    return {
        'today': float(today_sales),
        'yesterday': float(yesterday_sales),
        'percentage': 0.0,
        'is_positive': True
    }


def get_items_sold_today():
    """Get total items sold today"""
    try:
        client = get_supabase_client()
        today = datetime.now().date()
        
        # Get today's sales IDs
        sales_result = client.table('sales')\
            .select('id')\
            .gte('sales_date', f'{today}T00:00:00')\
            .lte('sales_date', f'{today}T23:59:59')\
            .eq('status', 'completed')\
            .execute()
        
        if not sales_result.data:
            return 0
        
        sale_ids = [sale['id'] for sale in sales_result.data]
        
        # Get items from those sales
        items_result = client.table('sales_items')\
            .select('quantity')\
            .in_('sale_id', sale_ids)\
            .execute()
        
        if items_result.data:
            return sum(item['quantity'] for item in items_result.data)
        return 0
    except Exception as e:
        print(f"Error getting items sold: {e}")
        return 0


def get_items_sold_yesterday():
    """Get total items sold yesterday"""
    try:
        client = get_supabase_client()
        yesterday = (datetime.now() - timedelta(days=1)).date()
        
        sales_result = client.table('sales')\
            .select('id')\
            .gte('sales_date', f'{yesterday}T00:00:00')\
            .lte('sales_date', f'{yesterday}T23:59:59')\
            .eq('status', 'completed')\
            .execute()
        
        if not sales_result.data:
            return 0
        
        sale_ids = [sale['id'] for sale in sales_result.data]
        
        items_result = client.table('sales_items')\
            .select('quantity')\
            .in_('sale_id', sale_ids)\
            .execute()
        
        if items_result.data:
            return sum(item['quantity'] for item in items_result.data)
        return 0
    except Exception as e:
        print(f"Error getting yesterday's items: {e}")
        return 0


def get_items_comparison():
    """Get items sold comparison"""
    today_items = get_items_sold_today()
    yesterday_items = get_items_sold_yesterday()
    
    if yesterday_items > 0:
        change = ((today_items - yesterday_items) / yesterday_items) * 100
        return {
            'today': today_items,
            'yesterday': yesterday_items,
            'percentage': round(change, 1),
            'is_positive': change >= 0
        }
    
    return {
        'today': today_items,
        'yesterday': yesterday_items,
        'percentage': 0.0,
        'is_positive': True
    }


def get_employee_stats():
    """Get employee statistics"""
    try:
        client = get_supabase_client()
        
        # Get all employees
        result = client.table('employees')\
            .select('status')\
            .execute()
        
        if result.data:
            total = len(result.data)
            active = len([e for e in result.data if e['status'] == 'active'])
            
            return {
                'active': active,
                'total': total,
                'percentage': round((active / total * 100), 1) if total > 0 else 0
            }
        
        return {'active': 0, 'total': 0, 'percentage': 0}
    except Exception as e:
        print(f"Error getting employee stats: {e}")
        return {'active': 0, 'total': 0, 'percentage': 0}


def get_low_stock_products(limit=None):
    """Get products with low stock"""
    try:
        client = get_supabase_client()
        
        # Get all products
        result = client.table('products')\
            .select('*')\
            .execute()
        
        if result.data:
            # Filter low stock items
            low_stock = [
                p for p in result.data 
                if p['current_stock'] <= p['low_stock_threshold']
            ]
            
            # Sort by stock percentage
            low_stock.sort(key=lambda x: (x['current_stock'] / x['low_stock_threshold']) if x['low_stock_threshold'] > 0 else 0)
            
            if limit:
                return low_stock[:limit]
            return low_stock
        
        return []
    except Exception as e:
        print(f"Error getting low stock products: {e}")
        return []


def get_recent_transactions(limit=6):
    """Get recent sales transactions"""
    try:
        client = get_supabase_client()
        
        result = client.table('sales')\
            .select('*')\
            .order('sales_date', desc=True)\
            .limit(limit)\
            .execute()
        
        return result.data if result.data else []
    except Exception as e:
        print(f"Error getting recent transactions: {e}")
        return []


def get_sales_trend_data(days=7):
    """Get sales trend data for chart"""
    try:
        client = get_supabase_client()
        
        # Get sales for last N days
        start_date = (datetime.now() - timedelta(days=days)).date()
        
        result = client.table('sales')\
            .select('sales_date, total_amount')\
            .gte('sales_date', f'{start_date}T00:00:00')\
            .eq('status', 'completed')\
            .execute()
        
        if not result.data:
            return []
        
        # Group by date
        daily_sales = {}
        for sale in result.data:
            sale_date = sale['sales_date'][:10]  # Get date part
            if sale_date not in daily_sales:
                daily_sales[sale_date] = 0
            daily_sales[sale_date] += float(sale['total_amount'])
        
        # Convert to list format for charts
        trend_data = [
            {'date': date, 'amount': amount}
            for date, amount in sorted(daily_sales.items())
        ]
        
        return trend_data
    except Exception as e:
        print(f"Error getting sales trend: {e}")
        return []


def get_products_by_category(category=None):
    """Get products, optionally filtered by category"""
    try:
        client = get_supabase_client()
        
        query = client.table('products').select('*')
        
        if category:
            query = query.eq('category', category)
        
        result = query.order('product_id').execute()
        
        return result.data if result.data else []
    except Exception as e:
        print(f"Error getting products: {e}")
        return []


def get_all_categories():
    """Get all unique product categories"""
    try:
        client = get_supabase_client()
        
        result = client.table('products')\
            .select('category')\
            .execute()
        
        if result.data:
            categories = list(set(p['category'] for p in result.data))
            # Sort in the order from screenshot
            category_order = [
                'Beverages',
                'Bakery & Snacks',
                'Health & Medicine',
                'Stationery',
                'Personal Care & Hygiene'
            ]
            sorted_categories = [c for c in category_order if c in categories]
            return sorted_categories
        
        return []
    except Exception as e:
        print(f"Error getting categories: {e}")
        return []


def search_products(query):
    """Search products by name or ID"""
    try:
        client = get_supabase_client()
        
        # Search by name or product_id
        result = client.table('products')\
            .select('*')\
            .or_(f'name.ilike.%{query}%,product_id.ilike.%{query}%')\
            .execute()
        
        return result.data if result.data else []
    except Exception as e:
        print(f"Error searching products: {e}")
        return []


def get_dashboard_metrics():
    """Get all dashboard metrics in one call"""
    return {
        'sales': get_sales_comparison(),
        'items': get_items_comparison(),
        'employees': get_employee_stats(),
        'low_stock': get_low_stock_products(limit=3),
        'recent_transactions': get_recent_transactions(limit=6),
        'sales_trend': get_sales_trend_data(days=7)
    }
