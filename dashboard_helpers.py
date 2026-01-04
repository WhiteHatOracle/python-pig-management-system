# dashboard_helpers.py
from datetime import date, datetime, timedelta
from models import db, Sows, Boars, Litter, ServiceRecords, Invoice, Expense
from flask_login import current_user


def get_herd_counts_by_stage(user_id):
    """
    Get current pig counts grouped by growth stage.
    This properly accounts for mortalities, sales, and cross-fostering.
    
    Returns:
        dict: {
            'preweaning': int,
            'weaner': int,
            'grower': int,
            'finisher': int,
            'total_piglets': int,
            'sows': int,
            'boars': int,
            'total_herd': int
        }
    """
    # Initialize counts
    stage_counts = {
        'preweaning': 0,
        'weaner': 0,
        'grower': 0,
        'finisher': 0,
        'total_piglets': 0,
        'sows': 0,
        'boars': 0,
        'total_herd': 0
    }
    
    # Count sows
    stage_counts['sows'] = Sows.query.filter_by(user_id=user_id).count()
    
    # Count boars
    stage_counts['boars'] = Boars.query.filter_by(user_id=user_id).count()
    
    # Get all active litters (litters with piglets still alive)
    sows = Sows.query.filter_by(user_id=user_id).all()
    
    for sow in sows:
        for service in sow.service_records:
            if service.litter:
                litter = service.litter
                alive = litter.current_alive
                
                if alive > 0:
                    stage = litter.stage
                    if stage in stage_counts:
                        stage_counts[stage] += alive
                    stage_counts['total_piglets'] += alive
    
    # Calculate total herd (sows + boars + all piglets)
    stage_counts['total_herd'] = (
        stage_counts['sows'] + 
        stage_counts['boars'] + 
        stage_counts['total_piglets']
    )
    
    return stage_counts


def get_active_litters_summary(user_id):
    """
    Get detailed summary of all active litters (those with piglets still alive).
    
    Returns:
        list: List of dicts with litter details
    """
    summary = []
    
    sows = Sows.query.filter_by(user_id=user_id).all()
    
    for sow in sows:
        for service in sow.service_records:
            if service.litter:
                litter = service.litter
                alive = litter.current_alive
                
                if alive > 0:
                    summary.append({
                        'litter_id': litter.id,
                        'sow_id': sow.sowID,
                        'sow_breed': sow.Breed,
                        'farrow_date': litter.farrowDate,
                        'age_days': litter.age_days,
                        'stage': litter.stage,
                        'born_alive': litter.bornAlive,
                        'fostered_in': litter.total_fostered_in,
                        'fostered_out': litter.total_fostered_out,
                        'mortalities': litter.total_mortalities,
                        'sold': litter.total_sold,
                        'current_alive': alive,
                        'survival_rate': litter.survival_rate,
                        'avg_weight': litter.latest_avg_weight or litter.averageWeight
                    })
    
    # Sort by farrow date (newest first)
    summary.sort(key=lambda x: x['farrow_date'], reverse=True)
    
    return summary


def get_upcoming_farrowings(user_id, days_ahead=30):
    """
    Get list of sows with upcoming farrowing dates.
    
    Args:
        user_id: The user's ID
        days_ahead: Number of days to look ahead (default 30)
    
    Returns:
        list: List of dicts with service record details
    """
    today = date.today()
    future_date = today + timedelta(days=days_ahead)
    
    upcoming = []
    
    # Get all service records for this user's sows that don't have a litter yet
    sows = Sows.query.filter_by(user_id=user_id).all()
    
    for sow in sows:
        for service in sow.service_records:
            # Only include if no litter recorded yet and due date is in the future
            if service.litter is None and service.due_date:
                if today <= service.due_date <= future_date:
                    upcoming.append({
                        'sow_id': sow.sowID,
                        'service_date': service.service_date.strftime('%d-%b-%Y') if service.service_date else '-',
                        'boar_used': service.boar_used or '-',
                        'checkup_date': service.checkup_date.strftime('%d-%b-%Y') if service.checkup_date else '-',
                        'litter_guard1_date': service.litter_guard1_date.strftime('%d-%b-%Y') if service.litter_guard1_date else '-',
                        'litter_guard2_date': service.litter_guard2_date.strftime('%d-%b-%Y') if service.litter_guard2_date else '-',
                        'due_date': service.due_date.strftime('%d-%b-%Y') if service.due_date else '-',
                        'days_until_due': (service.due_date - today).days
                    })
    
    # Sort by due date
    upcoming.sort(key=lambda x: x['days_until_due'])
    
    return upcoming


def get_mortality_summary(user_id, days=30):
    """
    Get mortality statistics for the specified period.
    
    Returns:
        dict: Mortality statistics by cause
    """
    from models import MortalityRecord
    
    cutoff_date = date.today() - timedelta(days=days)
    
    mortality_by_cause = {}
    total_deaths = 0
    
    sows = Sows.query.filter_by(user_id=user_id).all()
    
    for sow in sows:
        for service in sow.service_records:
            if service.litter:
                for mort in service.litter.mortality_records:
                    if mort.date >= cutoff_date:
                        cause = mort.cause or 'unknown'
                        if cause not in mortality_by_cause:
                            mortality_by_cause[cause] = 0
                        mortality_by_cause[cause] += mort.number_died
                        total_deaths += mort.number_died
    
    return {
        'by_cause': mortality_by_cause,
        'total': total_deaths,
        'period_days': days
    }


def get_sales_summary(user_id, days=30):
    """
    Get sales statistics for the specified period.
    
    Returns:
        dict: Sales statistics
    """
    from models import SaleRecord
    
    cutoff_date = date.today() - timedelta(days=days)
    
    total_sold = 0
    total_revenue = 0
    total_weight = 0
    sales_by_type = {}
    
    sows = Sows.query.filter_by(user_id=user_id).all()
    
    for sow in sows:
        for service in sow.service_records:
            if service.litter:
                for sale in service.litter.sale_records:
                    if sale.date >= cutoff_date:
                        total_sold += sale.number_sold
                        total_revenue += sale.total_amount or 0
                        total_weight += sale.total_weight or 0
                        
                        sale_type = sale.sale_type or 'market'
                        if sale_type not in sales_by_type:
                            sales_by_type[sale_type] = {'count': 0, 'revenue': 0}
                        sales_by_type[sale_type]['count'] += sale.number_sold
                        sales_by_type[sale_type]['revenue'] += sale.total_amount or 0
    
    return {
        'total_sold': total_sold,
        'total_revenue': total_revenue,
        'total_weight': total_weight,
        'avg_price_per_kg': total_revenue / total_weight if total_weight > 0 else 0,
        'by_type': sales_by_type,
        'period_days': days
    }


def get_theme_colors(theme='light'):
    """Return color scheme based on current theme"""
    if theme == 'dark':
        return {
            'text_primary': '#F7FAFC',      # Light text for dark bg
            'text_secondary': '#A0AEC0',     # Muted light text
            'text_muted': '#718096',         # Even more muted
            'bg_primary': '#1A202C',         # Dark background
            'bg_secondary': '#2D3748',       # Slightly lighter dark
            'grid_color': '#4A5568',         # Grid lines
            'border_color': '#4A5568',       # Borders
            'chart_bg': 'rgba(26, 32, 44, 0)',  # Transparent dark
            'positive': '#48BB78',           # Green for profit
            'negative': '#FC8181',           # Red for loss
            'revenue': '#48BB78',            # Revenue color
            'expenses': '#FC8181',           # Expenses color
            'pie_center_text': '#F7FAFC',    # Pie chart center text
        }
    else:
        return {
            'text_primary': '#1A202C',       # Dark text for light bg
            'text_secondary': '#4A5568',     # Muted dark text
            'text_muted': '#718096',         # Even more muted
            'bg_primary': '#FFFFFF',         # Light background
            'bg_secondary': '#F7FAFC',       # Slightly darker light
            'grid_color': '#E2E8F0',         # Grid lines
            'border_color': '#E2E8F0',       # Borders
            'chart_bg': 'rgba(255, 255, 255, 0)',  # Transparent light
            'positive': '#10B981',           # Green for profit
            'negative': '#EF4444',           # Red for loss
            'revenue': '#10B981',            # Revenue color
            'expenses': '#EF4444',           # Expenses color
            'pie_center_text': '#1A202C',    # Pie chart center text
        }

# Helper function to get financial data
def get_financial_data(period='90'):
    """Get revenue and expense data for the specified period"""
    from models import Invoice, Expense  # Import your models
    
    today = datetime.now().date()
    
    if period == 'all':
        start_date = datetime(2000, 1, 1).date()
    else:
        days = int(period)
        start_date = today - timedelta(days=days)
    
    # Get invoices (revenue)
    invoices = Invoice.query.filter(Invoice.date >= start_date).all()
    
    # Get expenses
    expenses = Expense.query.filter(Expense.date >= start_date).all()
    
    # Process revenue data
    revenue_by_month = {}
    for inv in invoices:
        month_key = inv.date.strftime('%Y-%m')
        if month_key not in revenue_by_month:
            revenue_by_month[month_key] = 0
        revenue_by_month[month_key] += float(inv.total_price or 0)
    
    # Process expense data
    expense_by_month = {}
    expense_by_category = {}
    for exp in expenses:
        month_key = exp.date.strftime('%Y-%m')
        if month_key not in expense_by_month:
            expense_by_month[month_key] = 0
        expense_by_month[month_key] += float(exp.amount or 0)
        
        # Category breakdown
        category = exp.category or 'Other'
        if category not in expense_by_category:
            expense_by_category[category] = 0
        expense_by_category[category] += float(exp.amount or 0)
    
    # Calculate totals
    total_revenue = sum(revenue_by_month.values())
    total_expenses = sum(expense_by_month.values())
    net_profit = total_revenue - total_expenses
    profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    return {
        'revenue_by_month': revenue_by_month,
        'expense_by_month': expense_by_month,
        'expense_by_category': expense_by_category,
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'profit_margin': profit_margin,
    }

