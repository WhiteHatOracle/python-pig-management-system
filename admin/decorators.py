from functools import wraps
from flask import redirect, url_for, flash, session, request
from models import AdminUser

def admin_required(f):
    """Decorator to require admin login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_id = session.get('admin_id')
        if not admin_id:
            flash('Please log in to access the admin panel.', 'error')
            return redirect(url_for('admin.login', next=request.url))
        
        admin = AdminUser.query.get(admin_id)
        if not admin or not admin.is_active:
            session.pop('admin_id', None)
            flash('Your admin session has expired.', 'error')
            return redirect(url_for('admin.login'))
        
        return f(*args, **kwargs)
    return decorated_function


def super_admin_required(f):
    """Decorator to require super admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_id = session.get('admin_id')
        if not admin_id:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('admin.login'))
        
        admin = AdminUser.query.get(admin_id)
        if not admin or not admin.is_super_admin:
            flash('You need super admin privileges to access this page.', 'error')
            return redirect(url_for('admin.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function