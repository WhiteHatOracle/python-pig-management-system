"""
Initialize default system settings.
Run this once after setting up the admin panel.
"""

from models import db, SystemSetting


DEFAULT_SETTINGS = {
    'site_name': {
        'value': 'Pig Management System',
        'description': 'The name displayed in the browser tab and emails'
    },
    'support_email': {
        'value': '',
        'description': 'Email address for user support inquiries'
    },
    'max_sows': {
        'value': '0',
        'description': 'Maximum sows per user (0 = unlimited)'
    },
    'allow_registration': {
        'value': 'true',
        'description': 'Enable or disable new user registrations'
    },
    'require_verification': {
        'value': 'true',
        'description': 'Require email verification before accessing the app'
    },
    'allow_google': {
        'value': 'true',
        'description': 'Enable Google OAuth login option'
    },
    'maintenance_mode': {
        'value': 'false',
        'description': 'Put the site in maintenance mode'
    },
    'maintenance_message': {
        'value': 'We are currently performing scheduled maintenance. Please check back soon.',
        'description': 'Message shown during maintenance'
    }
}


def init_default_settings():
    """Initialize default settings if they don't exist"""
    for key, data in DEFAULT_SETTINGS.items():
        existing = SystemSetting.query.filter_by(key=key).first()
        if not existing:
            setting = SystemSetting(
                key=key,
                value=data['value'],
                description=data['description']
            )
            db.session.add(setting)
            print(f"  ✓ Created setting: {key}")
    
    db.session.commit()
    print("\n✅ Default settings initialized!")


if __name__ == '__main__':
    from app import app
    with app.app_context():
        init_default_settings()