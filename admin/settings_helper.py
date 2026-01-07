"""
Settings helper to retrieve and use system settings throughout the app.
"""

from models import db, SystemSetting
from functools import lru_cache
import time

# Cache settings for 60 seconds to avoid constant DB queries
_settings_cache = {}
_cache_time = 0
CACHE_DURATION = 60  # seconds


def get_setting(key, default=None):
    """Get a single setting value"""
    global _settings_cache, _cache_time
    
    # Refresh cache if expired
    if time.time() - _cache_time > CACHE_DURATION:
        refresh_settings_cache()
    
    return _settings_cache.get(key, default)


def get_all_settings():
    """Get all settings as a dictionary"""
    global _settings_cache, _cache_time
    
    if time.time() - _cache_time > CACHE_DURATION:
        refresh_settings_cache()
    
    return _settings_cache.copy()


def refresh_settings_cache():
    """Refresh the settings cache from database"""
    global _settings_cache, _cache_time
    
    try:
        settings = SystemSetting.query.all()
        _settings_cache = {s.key: s.value for s in settings}
        _cache_time = time.time()
    except:
        # If DB error, keep existing cache
        pass


def set_setting(key, value, description=None):
    """Set a setting value"""
    global _settings_cache, _cache_time
    
    setting = SystemSetting.query.filter_by(key=key).first()
    if setting:
        setting.value = str(value)
        if description:
            setting.description = description
    else:
        setting = SystemSetting(key=key, value=str(value), description=description)
        db.session.add(setting)
    
    db.session.commit()
    
    # Update cache
    _settings_cache[key] = str(value)
    
    return setting


def is_enabled(key, default=True):
    """Check if a boolean setting is enabled"""
    value = get_setting(key)
    if value is None:
        return default
    return value.lower() in ('true', '1', 'yes', 'on')


# ==================== SPECIFIC SETTING HELPERS ====================

def is_registration_allowed():
    """Check if new user registration is allowed"""
    return is_enabled('allow_registration', default=True)


def is_email_verification_required():
    """Check if email verification is required"""
    return is_enabled('require_verification', default=True)


def is_google_login_allowed():
    """Check if Google OAuth login is allowed"""
    return is_enabled('allow_google', default=True)


def is_maintenance_mode():
    """Check if site is in maintenance mode"""
    return is_enabled('maintenance_mode', default=False)


def get_maintenance_message():
    """Get the maintenance mode message"""
    return get_setting('maintenance_message', 'We are currently performing scheduled maintenance. Please check back soon.')


def get_site_name():
    """Get the site name"""
    return get_setting('site_name', 'Pig Management System')


def get_support_email():
    """Get the support email"""
    return get_setting('support_email', '')


def get_max_sows_per_user():
    """Get maximum sows allowed per user (0 = unlimited)"""
    try:
        return int(get_setting('max_sows', '0'))
    except:
        return 0