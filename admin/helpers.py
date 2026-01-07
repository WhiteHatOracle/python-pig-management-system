from datetime import datetime, timedelta, timezone
from sqlalchemy import func, desc
from models import db, User, Boars, Sows, Litter, Invoice, Expense, PageView, ActivityLog, MortalityRecord, SaleRecord
import json

def get_dashboard_stats():
    """Get all dashboard statistics"""
    today = datetime.now(timezone.utc).date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # User stats
    total_users = User.query.count()
    verified_users = User.query.filter_by(is_verified=True).count()
    new_users_week = User.query.filter(func.date(User.created_at) >= week_ago).count()
    new_users_month = User.query.filter(func.date(User.created_at) >= month_ago).count()
    google_users = User.query.filter(User.google_id.isnot(None)).count()
    
    # Pig stats (across all users)
    total_sows = Sows.query.count()
    total_boars = Boars.query.count()
    total_litters = Litter.query.count()
    
    # Active litters by stage
    all_litters = Litter.query.all()
    stages = {'preweaning': 0, 'weaner': 0, 'grower': 0, 'finisher': 0}
    total_piglets = 0
    for litter in all_litters:
        stage = litter.stage
        if stage in stages:
            stages[stage] += litter.current_alive
        total_piglets += litter.current_alive
    
    # Financial stats
    total_revenue = db.session.query(func.sum(Invoice.total_price)).scalar() or 0
    total_expenses = db.session.query(func.sum(Expense.amount)).scalar() or 0
    
    # Traffic stats (today)
    today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
    today_views = PageView.query.filter(PageView.timestamp >= today_start).count()
    week_views = PageView.query.filter(PageView.timestamp >= datetime.combine(week_ago, datetime.min.time()).replace(tzinfo=timezone.utc)).count()
    
    # Unique visitors today
    unique_today = db.session.query(func.count(func.distinct(PageView.ip_address))).filter(
        PageView.timestamp >= today_start
    ).scalar() or 0
    
    return {
        'users': {
            'total': total_users,
            'verified': verified_users,
            'unverified': total_users - verified_users,
            'new_week': new_users_week,
            'new_month': new_users_month,
            'google_users': google_users,
            'email_users': total_users - google_users,
        },
        'pigs': {
            'total_sows': total_sows,
            'total_boars': total_boars,
            'total_litters': total_litters,
            'total_piglets': total_piglets,
            'stages': stages,
        },
        'financial': {
            'total_revenue': total_revenue,
            'total_expenses': total_expenses,
            'profit': total_revenue - total_expenses,
        },
        'traffic': {
            'today_views': today_views,
            'week_views': week_views,
            'unique_today': unique_today,
        }
    }


def get_traffic_data(days=30):
    """Get traffic data for charts"""
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    # Daily page views
    daily_views = db.session.query(
        func.date(PageView.timestamp).label('date'),
        func.count(PageView.id).label('views')
    ).filter(
        PageView.timestamp >= start_date
    ).group_by(
        func.date(PageView.timestamp)
    ).order_by(
        func.date(PageView.timestamp)
    ).all()
    
    # Top pages
    top_pages = db.session.query(
        PageView.path,
        func.count(PageView.id).label('views')
    ).filter(
        PageView.timestamp >= start_date
    ).group_by(
        PageView.path
    ).order_by(
        desc(func.count(PageView.id))
    ).limit(10).all()
    
    # Device breakdown
    devices = db.session.query(
        PageView.device_type,
        func.count(PageView.id).label('count')
    ).filter(
        PageView.timestamp >= start_date,
        PageView.device_type.isnot(None)
    ).group_by(
        PageView.device_type
    ).all()
    
    # Browser breakdown
    browsers = db.session.query(
        PageView.browser,
        func.count(PageView.id).label('count')
    ).filter(
        PageView.timestamp >= start_date,
        PageView.browser.isnot(None)
    ).group_by(
        PageView.browser
    ).order_by(
        desc(func.count(PageView.id))
    ).limit(5).all()
    
    return {
        'daily_views': [(str(d.date), d.views) for d in daily_views],
        'top_pages': [(p.path, p.views) for p in top_pages],
        'devices': {d.device_type: d.count for d in devices if d.device_type},
        'browsers': {b.browser: b.count for b in browsers if b.browser},
    }


def get_user_growth_data(days=30):
    """Get user registration data for charts"""
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    daily_signups = db.session.query(
        func.date(User.created_at).label('date'),
        func.count(User.id).label('signups')
    ).filter(
        User.created_at >= start_date
    ).group_by(
        func.date(User.created_at)
    ).order_by(
        func.date(User.created_at)
    ).all()
    
    return [(str(d.date), d.signups) for d in daily_signups]


def get_recent_activity(limit=20):
    """Get recent activity logs"""
    activities = ActivityLog.query.order_by(
        desc(ActivityLog.timestamp)
    ).limit(limit).all()
    
    return activities


def log_activity(action, entity_type=None, entity_id=None, details=None, user_id=None, admin_id=None, ip_address=None):
    """Log an activity"""
    from flask import request
    
    log = ActivityLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=json.dumps(details) if details else None,
        user_id=user_id,
        admin_id=admin_id,
        ip_address=ip_address or request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    return log