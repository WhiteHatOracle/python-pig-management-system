# decorators.py (in your main app folder, not admin/)

from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user, login_required as flask_login_required

def login_required(f):
    """
    Custom login_required that also checks email verification if required.
    This replaces Flask-Login's login_required.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # First check if logged in (using Flask-Login's check)
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('signin'))
        
        # Then check verification if setting is enabled
        try:
            from admin.settings_helper import is_email_verification_required
            if is_email_verification_required() and not current_user.is_verified:
                flash('Please verify your email to access this feature.', 'warning')
                return redirect(url_for('verification_pending'))
        except:
            # If settings not available, skip verification check
            pass
        
        return f(*args, **kwargs)
    return decorated_function


def login_required_no_verify(f):
    """
    Login required but doesn't check verification.
    Use this for routes that unverified users should access (like resend verification).
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('signin'))
        return f(*args, **kwargs)
    return decorated_function