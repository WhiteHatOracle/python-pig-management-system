"""
Middleware to enforce system settings across the app.
"""

from flask import redirect, url_for, render_template_string, request, session, g
from functools import wraps
from admin.settings_helper import (
    is_maintenance_mode, 
    get_maintenance_message,
    is_registration_allowed,
    is_google_login_allowed,
    get_site_name
)


# ==================== MAINTENANCE MODE TEMPLATE ====================
MAINTENANCE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Maintenance | {{ site_name }}</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Poppins', sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #1A202C 0%, #2D3748 100%);
            color: #fff;
            padding: 2rem;
        }
        .maintenance-container {
            text-align: center;
            max-width: 500px;
        }
        .maintenance-icon {
            font-size: 5rem;
            margin-bottom: 1.5rem;
            animation: bounce 2s infinite;
        }
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }
        .maintenance-title {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 1rem;
        }
        .maintenance-message {
            font-size: 1.125rem;
            color: #A0AEC0;
            line-height: 1.6;
            margin-bottom: 2rem;
        }
        .maintenance-footer {
            font-size: 0.875rem;
            color: #718096;
        }
        .admin-link {
            color: #00A86B;
            text-decoration: none;
        }
        .admin-link:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="maintenance-container">
        <div class="maintenance-icon">🔧</div>
        <h1 class="maintenance-title">Under Maintenance</h1>
        <p class="maintenance-message">{{ message }}</p>
        <p class="maintenance-footer">
            <a href="/admin/login" class="admin-link">Admin Access</a>
        </p>
    </div>
</body>
</html>
'''


def init_settings_middleware(app):
    """Initialize settings middleware for the Flask app"""
    
    @app.before_request
    def check_maintenance_mode():
        """Check if site is in maintenance mode"""
        # Skip for static files and admin routes
        if request.path.startswith('/static') or request.path.startswith('/admin'):
            return None
        
        # Skip for API endpoints if needed
        if request.path.startswith('/api'):
            return None
        
        # Check maintenance mode
        if is_maintenance_mode():
            # Allow if admin is logged in
            if session.get('admin_id'):
                return None
            
            return render_template_string(
                MAINTENANCE_TEMPLATE,
                site_name=get_site_name(),
                message=get_maintenance_message()
            ), 503
    
    @app.context_processor
    def inject_settings():
        """Inject common settings into all templates"""
        return {
            'site_name': get_site_name(),
            'registration_allowed': is_registration_allowed(),
            'google_login_allowed': is_google_login_allowed(),
        }


def registration_required(f):
    """Decorator to check if registration is allowed"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_registration_allowed():
            from flask import flash
            flash('New registrations are currently disabled.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def google_login_required(f):
    """Decorator to check if Google login is allowed"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_google_login_allowed():
            from flask import flash
            flash('Google login is currently disabled.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function