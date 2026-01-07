from flask import render_template, redirect, url_for, flash, request, session, jsonify
from datetime import datetime, timezone, timedelta
from sqlalchemy import desc, func
from admin import admin_bp
from admin.decorators import admin_required, super_admin_required
from admin.helpers import (
    get_dashboard_stats, get_traffic_data, get_user_growth_data,
    get_recent_activity, log_activity
)
from models import db, User, AdminUser, Boars, Sows, Litter, Invoice, Expense, PageView, ActivityLog, SystemSetting
from werkzeug.security import generate_password_hash


# ==================== AUTHENTICATION ====================

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    # If already logged in, redirect to dashboard
    if session.get('admin_id'):
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        admin = AdminUser.query.filter(
            (AdminUser.username == username) | (AdminUser.email == username)
        ).first()
        
        if admin and admin.check_password(password):
            if not admin.is_active:
                flash('Your account has been deactivated.', 'error')
                return render_template('admin/login.html')
            
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            session.permanent = True
            
            # Update last login
            admin.last_login = datetime.now(timezone.utc)
            db.session.commit()
            
            # Log activity
            log_activity('admin_login', admin_id=admin.id)
            
            flash(f'Welcome back, {admin.username}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin.dashboard'))
        else:
            flash('Invalid username or password.', 'error')
            log_activity('admin_login_failed', details={'username': username})
    
    return render_template('admin/login.html')


@admin_bp.route('/logout')
def logout():
    """Admin logout"""
    admin_id = session.get('admin_id')
    if admin_id:
        log_activity('admin_logout', admin_id=admin_id)
    
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('admin.login'))


# ==================== DASHBOARD ====================

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Main admin dashboard"""
    stats = get_dashboard_stats()
    recent_activity = get_recent_activity(10)
    user_growth = get_user_growth_data(14)  # Last 14 days
    
    return render_template('admin/dashboard.html',
        stats=stats,
        recent_activity=recent_activity,
        user_growth=user_growth
    )


# ==================== USER MANAGEMENT ====================

@admin_bp.route('/users')
@admin_required
def users():
    """User management page"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search = request.args.get('search', '').strip()
    filter_type = request.args.get('filter', 'all')
    
    query = User.query
    
    # Apply search
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%')) |
            (User.name.ilike(f'%{search}%'))
        )
    
    # Apply filters
    if filter_type == 'verified':
        query = query.filter_by(is_verified=True)
    elif filter_type == 'unverified':
        query = query.filter_by(is_verified=False)
    elif filter_type == 'google':
        query = query.filter(User.google_id.isnot(None))
    elif filter_type == 'email':
        query = query.filter(User.google_id.is_(None))
    
    # Order and paginate
    users = query.order_by(desc(User.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/users.html',
        users=users,
        search=search,
        filter_type=filter_type
    )


@admin_bp.route('/users/<int:user_id>')
@admin_required
def user_detail(user_id):
    """User detail page"""
    user = User.query.get_or_404(user_id)
    
    # Get user's data counts
    sow_count = Sows.query.filter_by(user_id=user_id).count()
    boar_count = Boars.query.filter_by(user_id=user_id).count()
    invoice_count = Invoice.query.filter_by(user_id=user_id).count()
    expense_count = Expense.query.filter_by(user_id=user_id).count()
    
    # Get recent activity for this user
    activity = ActivityLog.query.filter_by(user_id=user_id).order_by(
        desc(ActivityLog.timestamp)
    ).limit(20).all()
    
    return render_template('admin/user_detail.html',
        user=user,
        sow_count=sow_count,
        boar_count=boar_count,
        invoice_count=invoice_count,
        expense_count=expense_count,
        activity=activity
    )


@admin_bp.route('/users/<int:user_id>/toggle-verify', methods=['POST'])
@admin_required
def toggle_user_verify(user_id):
    """Toggle user verification status"""
    user = User.query.get_or_404(user_id)
    user.is_verified = not user.is_verified
    db.session.commit()
    
    log_activity(
        'user_verification_toggled',
        entity_type='user',
        entity_id=user_id,
        details={'verified': user.is_verified},
        admin_id=session.get('admin_id')
    )
    
    flash(f'User {user.username} is now {"verified" if user.is_verified else "unverified"}.', 'success')
    return redirect(url_for('admin.user_detail', user_id=user_id))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@super_admin_required
def delete_user(user_id):
    """Delete a user"""
    user = User.query.get_or_404(user_id)
    username = user.username
    
    db.session.delete(user)
    db.session.commit()
    
    log_activity(
        'user_deleted',
        entity_type='user',
        entity_id=user_id,
        details={'username': username},
        admin_id=session.get('admin_id')
    )
    
    flash(f'User {username} has been deleted.', 'success')
    return redirect(url_for('admin.users'))


# ==================== TRAFFIC ANALYTICS ====================

@admin_bp.route('/traffic')
@admin_required
def traffic():
    """Traffic analytics page"""
    days = request.args.get('days', 30, type=int)
    traffic_data = get_traffic_data(days)
    
    # Get some quick stats
    today = datetime.now(timezone.utc).date()
    today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
    
    today_views = PageView.query.filter(PageView.timestamp >= today_start).count()
    avg_response_time = db.session.query(func.avg(PageView.response_time)).filter(
        PageView.timestamp >= today_start,
        PageView.response_time.isnot(None)
    ).scalar() or 0
    
    return render_template('admin/traffic.html',
        traffic_data=traffic_data,
        days=days,
        today_views=today_views,
        avg_response_time=round(avg_response_time, 2)
    )


# ==================== ACTIVITY LOGS ====================

@admin_bp.route('/activity')
@admin_required
def activity():
    """Activity logs page"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    action_filter = request.args.get('action', '')
    
    query = ActivityLog.query
    
    if action_filter:
        query = query.filter(ActivityLog.action.ilike(f'%{action_filter}%'))
    
    logs = query.order_by(desc(ActivityLog.timestamp)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get unique action types for filter dropdown
    action_types = db.session.query(ActivityLog.action).distinct().all()
    action_types = [a[0] for a in action_types]
    
    return render_template('admin/activity.html',
        logs=logs,
        action_filter=action_filter,
        action_types=action_types
    )


# ==================== SETTINGS ====================
@admin_bp.route('/settings', methods=['GET', 'POST'])
@super_admin_required
def settings():
    """System settings page"""
    from admin.settings_helper import refresh_settings_cache
    
    if request.method == 'POST':
        # Define boolean settings (checkboxes)
        boolean_settings = [
            'allow_registration',
            'require_verification', 
            'allow_google',
            'maintenance_mode'
        ]
        
        # Process all settings
        for key in ['site_name', 'support_email', 'max_sows', 'maintenance_message']:
            full_key = f'setting_{key}'
            if full_key in request.form:
                setting = SystemSetting.query.filter_by(key=key).first()
                if setting:
                    setting.value = request.form[full_key]
                else:
                    setting = SystemSetting(key=key, value=request.form[full_key])
                    db.session.add(setting)
        
        # Process boolean settings (checkboxes)
        for key in boolean_settings:
            full_key = f'setting_{key}'
            # Checkbox is 'on' if checked, not present if unchecked
            value = 'true' if full_key in request.form else 'false'
            
            setting = SystemSetting.query.filter_by(key=key).first()
            if setting:
                setting.value = value
            else:
                setting = SystemSetting(key=key, value=value)
                db.session.add(setting)
        
        db.session.commit()
        
        # Refresh the settings cache
        refresh_settings_cache()
        
        log_activity('settings_updated', admin_id=session.get('admin_id'))
        flash('Settings updated successfully.', 'success')
        
        return redirect(url_for('admin.settings'))
    
    # Get current settings
    settings_dict = {s.key: s.value for s in SystemSetting.query.all()}
    
    return render_template('admin/settings.html', settings=settings_dict)

# ==================== ADMIN MANAGEMENT ====================

@admin_bp.route('/admins')
@super_admin_required
def admins():
    """Admin management page"""
    admins = AdminUser.query.order_by(AdminUser.created_at).all()
    return render_template('admin/admins.html', admins=admins)


@admin_bp.route('/admins/create', methods=['GET', 'POST'])
@super_admin_required
def create_admin():
    """Create new admin"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        is_super = request.form.get('is_super_admin') == 'on'
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('admin/create_admin.html')
        
        if AdminUser.query.filter((AdminUser.username == username) | (AdminUser.email == email)).first():
            flash('Username or email already exists.', 'error')
            return render_template('admin/create_admin.html')
        
        admin = AdminUser(username=username, email=email, is_super_admin=is_super)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        
        log_activity(
            'admin_created',
            entity_type='admin',
            entity_id=admin.id,
            admin_id=session.get('admin_id')
        )
        
        flash(f'Admin {username} created successfully.', 'success')
        return redirect(url_for('admin.admins'))
    
    return render_template('admin/create_admin.html')


# ==================== API ENDPOINTS ====================

@admin_bp.route('/api/stats')
@admin_required
def api_stats():
    """API endpoint for dashboard stats (for real-time updates)"""
    stats = get_dashboard_stats()
    return jsonify(stats)


@admin_bp.route('/api/traffic/<int:days>')
@admin_required
def api_traffic(days):
    """API endpoint for traffic data"""
    data = get_traffic_data(days)
    return jsonify(data)