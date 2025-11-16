"""
Report data aggregation utilities for SmartRetail
Handles calculations for sales analytics, product performance, and financial summaries
"""

from datetime import datetime, timedelta
from decimal import Decimal
from ..supabase_client import get_supabase_client
import logging

logger = logging.getLogger(__name__)


def format_currency(amount):
    """Format amount as Malaysian Ringgit"""
    if amount is None:
        return "RM0.00"
    return f"RM{float(amount):,.2f}"


def calculate_percentage_change(current, previous):
    """Calculate percentage change between two values"""
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    
    change = ((current - previous) / previous) * 100
    return round(change, 1)


def get_date_range(period='today'):
    """Get start and end dates for a period"""
    now = datetime.now()
    
    if period == 'today':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif period == 'week':
        # Start of current week (Monday)
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif period == 'month':
        # Start of current month
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now
    else:
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    
    return start, end


def get_best_selling_products(limit=10):
    """
    Get best-selling products with turnover and growth percentage
    
    Returns list of dicts with:
    - product_name
    - product_id
    - category
    - total_sold (units)
    - turnover (formatted currency)
    - increase_by (percentage)
    """
    try:
        client = get_supabase_client()
        
        # Get current month date range
        now = datetime.now()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Get previous month date range
        if now.month == 1:
            previous_month_start = datetime(now.year - 1, 12, 1)
            previous_month_end = datetime(now.year, 1, 1) - timedelta(seconds=1)
        else:
            previous_month_start = datetime(now.year, now.month - 1, 1)
            previous_month_end = current_month_start - timedelta(seconds=1)
        
        # Get all completed sales with items from current month
        current_sales = client.table('sales')\
            .select('*, sales_items(*, products(*))')\
            .eq('status', 'completed')\
            .gte('sales_date', current_month_start.isoformat())\
            .execute()
        
        # Get previous month sales for comparison
        previous_sales = client.table('sales')\
            .select('*, sales_items(*, products(*))')\
            .eq('status', 'completed')\
            .gte('sales_date', previous_month_start.isoformat())\
            .lte('sales_date', previous_month_end.isoformat())\
            .execute()
        
        # Aggregate current month data by product
        current_products = {}
        if current_sales.data:
            for sale in current_sales.data:
                if sale.get('sales_items'):
                    for item in sale['sales_items']:
                        if item.get('products'):
                            product = item['products']
                            product_id = product['product_id']
                            
                            if product_id not in current_products:
                                current_products[product_id] = {
                                    'product_name': product['name'],
                                    'product_id': product_id,
                                    'category': product['category'],
                                    'total_sold': 0,
                                    'turnover': 0
                                }
                            
                            current_products[product_id]['total_sold'] += item['quantity']
                            current_products[product_id]['turnover'] += float(item['subtotal'])
        
        # Aggregate previous month data by product
        previous_products = {}
        if previous_sales.data:
            for sale in previous_sales.data:
                if sale.get('sales_items'):
                    for item in sale['sales_items']:
                        if item.get('products'):
                            product_id = item['products']['product_id']
                            
                            if product_id not in previous_products:
                                previous_products[product_id] = {'turnover': 0}
                            
                            previous_products[product_id]['turnover'] += float(item['subtotal'])
        
        # Calculate percentage changes
        best_products = []
        for product_id, data in current_products.items():
            previous_turnover = previous_products.get(product_id, {}).get('turnover', 0)
            increase_by = calculate_percentage_change(data['turnover'], previous_turnover)
            
            best_products.append({
                'product_name': data['product_name'],
                'product_id': data['product_id'],
                'category': data['category'],
                'total_sold': f"{data['total_sold']} unit",
                'turnover': format_currency(data['turnover']),
                'turnover_raw': data['turnover'],
                'increase_by': f"{increase_by}%"
            })
        
        # Sort by turnover (descending) and limit
        best_products.sort(key=lambda x: x['turnover_raw'], reverse=True)
        return best_products[:limit]
        
    except Exception as e:
        logger.error(f"Error getting best selling products: {str(e)}")
        return []


def get_best_selling_categories(limit=10):
    """
    Get best-selling categories with turnover and growth percentage
    
    Returns list of dicts with:
    - category
    - turnover (formatted currency)
    - increase_by (percentage)
    """
    try:
        client = get_supabase_client()
        
        # Get current month date range
        now = datetime.now()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Get previous month date range
        if now.month == 1:
            previous_month_start = datetime(now.year - 1, 12, 1)
            previous_month_end = datetime(now.year, 1, 1) - timedelta(seconds=1)
        else:
            previous_month_start = datetime(now.year, now.month - 1, 1)
            previous_month_end = current_month_start - timedelta(seconds=1)
        
        # Get all completed sales with items from current month
        current_sales = client.table('sales')\
            .select('*, sales_items(*, products(category))')\
            .eq('status', 'completed')\
            .gte('sales_date', current_month_start.isoformat())\
            .execute()
        
        # Get previous month sales for comparison
        previous_sales = client.table('sales')\
            .select('*, sales_items(*, products(category))')\
            .eq('status', 'completed')\
            .gte('sales_date', previous_month_start.isoformat())\
            .lte('sales_date', previous_month_end.isoformat())\
            .execute()
        
        # Aggregate current month data by category
        current_categories = {}
        if current_sales.data:
            for sale in current_sales.data:
                if sale.get('sales_items'):
                    for item in sale['sales_items']:
                        if item.get('products'):
                            category = item['products']['category']
                            
                            if category not in current_categories:
                                current_categories[category] = 0
                            
                            current_categories[category] += float(item['subtotal'])
        
        # Aggregate previous month data by category
        previous_categories = {}
        if previous_sales.data:
            for sale in previous_sales.data:
                if sale.get('sales_items'):
                    for item in sale['sales_items']:
                        if item.get('products'):
                            category = item['products']['category']
                            
                            if category not in previous_categories:
                                previous_categories[category] = 0
                            
                            previous_categories[category] += float(item['subtotal'])
        
        # Calculate percentage changes
        best_categories = []
        for category, turnover in current_categories.items():
            previous_turnover = previous_categories.get(category, 0)
            increase_by = calculate_percentage_change(turnover, previous_turnover)
            
            best_categories.append({
                'category': category,
                'turnover': format_currency(turnover),
                'turnover_raw': turnover,
                'increase_by': f"{increase_by}%"
            })
        
        # Sort by turnover (descending) and limit
        best_categories.sort(key=lambda x: x['turnover_raw'], reverse=True)
        return best_categories[:limit]
        
    except Exception as e:
        logger.error(f"Error getting best selling categories: {str(e)}")
        return []


def get_low_stock_products(limit=3):
    """
    Get products with low stock levels
    
    Returns list of dicts with:
    - product_name
    - quantity (formatted as current/threshold)
    - current_stock (for charting)
    """
    try:
        client = get_supabase_client()
        
        # Get all products
        products = client.table('products')\
            .select('*')\
            .execute()
        
        # Filter low stock products
        low_stock = []
        if products.data:
            for product in products.data:
                current_stock = product['current_stock']
                low_stock_threshold = product['low_stock_threshold']
                
                if current_stock <= low_stock_threshold:
                    low_stock.append({
                        'product_name': product['name'],
                        'product_id': product.get('product_id', 'N/A'),
                        'quantity': f"{current_stock}/{low_stock_threshold}",
                        'current_stock': current_stock,
                        'low_stock_threshold': low_stock_threshold
                    })
        
        # Sort by current stock (ascending) and limit
        low_stock.sort(key=lambda x: x['current_stock'])
        return low_stock[:limit]
        
    except Exception as e:
        logger.error(f"Error getting low stock products: {str(e)}")
        return []


def get_total_sales(period='today'):
    """
    Calculate total sales for a specific period
    
    Args:
        period: 'today', 'week', or 'month'
    
    Returns:
        Formatted currency string
    """
    try:
        client = get_supabase_client()
        start, end = get_date_range(period)
        
        # Get completed sales in the period
        sales = client.table('sales')\
            .select('total_amount')\
            .eq('status', 'completed')\
            .gte('sales_date', start.isoformat())\
            .lte('sales_date', end.isoformat())\
            .execute()
        
        total = 0
        if sales.data:
            for sale in sales.data:
                total += float(sale['total_amount'])
        
        return format_currency(total)
        
    except Exception as e:
        logger.error(f"Error calculating total sales for {period}: {str(e)}")
        return format_currency(0)


def get_profit_revenue_trend(months=7):
    """
    Generate monthly profit and revenue data for line chart
    Calculate actual profit based on product costs (not hardcoded percentage)
    
    Args:
        months: Number of months to include (default 7)
    
    Returns:
        Dict with labels, revenue, profit, and costs arrays for Chart.js
    """
    try:
        client = get_supabase_client()
        now = datetime.now()
        
        # Generate month labels
        month_labels = []
        month_revenue = []
        month_costs = []
        month_profit = []
        
        for i in range(months - 1, -1, -1):
            # Calculate the month
            target_month = now.month - i
            target_year = now.year
            
            while target_month <= 0:
                target_month += 12
                target_year -= 1
            
            # Create date for start of month
            month_date = datetime(target_year, target_month, 1)
            month_labels.append(month_date.strftime('%b'))
            
            # Calculate month range
            if target_month == 12:
                next_month = datetime(target_year + 1, 1, 1)
            else:
                next_month = datetime(target_year, target_month + 1, 1)
            
            month_start = month_date
            month_end = next_month - timedelta(seconds=1)
            
            # Get sales with items for this month
            sales = client.table('sales')\
                .select('*, sales_items(*, products(*))')\
                .eq('status', 'completed')\
                .gte('sales_date', month_start.isoformat())\
                .lte('sales_date', month_end.isoformat())\
                .execute()
            
            # Calculate revenue and costs
            total_revenue = 0
            total_cost = 0
            
            if sales.data:
                for sale in sales.data:
                    sale_revenue = float(sale['total_amount'])
                    sale_cost = 0
                    
                    # Add to revenue
                    total_revenue += sale_revenue
                    
                    # Calculate cost from items
                    if sale.get('sales_items') and len(sale['sales_items']) > 0:
                        for item in sale['sales_items']:
                            quantity = item['quantity']
                            unit_price = item.get('unit_price', 0)
                            
                            # Use product cost if the field exists, otherwise estimate at 30% of unit price
                            if item.get('products') and 'cost' in item['products'] and item['products']['cost']:
                                item_cost = float(item['products']['cost']) * quantity
                            else:
                                # Fallback: estimate cost as 30% of selling price
                                item_cost = float(unit_price) * quantity * 0.30
                            
                            sale_cost += item_cost
                    else:
                        # No items found - estimate cost as 30% of sale total (fallback for legacy data)
                        sale_cost = sale_revenue * 0.30
                    
                    total_cost += sale_cost
            
            # Calculate profit
            total_profit = total_revenue - total_cost
            
            month_revenue.append(round(total_revenue, 2))
            month_costs.append(round(total_cost, 2))
            month_profit.append(round(total_profit, 2))
        
        return {
            'labels': month_labels,
            'revenue': month_revenue,
            'costs': month_costs,
            'profit': month_profit
        }
        
    except Exception as e:
        logger.error(f"Error generating profit/revenue trend: {str(e)}")
        return {
            'labels': [],
            'revenue': [],
            'costs': [],
            'profit': []
        }


def get_report_date():
    """Get formatted report date"""
    now = datetime.now()
    return now.strftime('%d %B, %Y')


def get_report_metadata():
    """Generate report ID and reference number"""
    now = datetime.now()
    
    # Generate report ID (format: AB2324-01)
    month_code = now.strftime('%m')
    year_code = now.strftime('%y')
    report_id = f"AB{month_code}{year_code}-01"
    
    # Generate reference number (format: INV-057)
    ref_number = f"INV-{now.strftime('%j')}"  # Day of year
    
    return {
        'report_id': report_id,
        'reference': ref_number,
        'date': get_report_date()
    }
