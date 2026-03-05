from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from extensions import db
from notifications.models import Notification, NotificationPreference, DEFAULT_NOTIFICATION_SETTINGS
from notifications.services import NotificationService

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')


@notifications_bp.route('/')
@login_required
def notification_list():
    """Display all notifications"""
    # Generate new notifications on page load
    NotificationService.generate_all_notifications(current_user.id)
    
    notifications = NotificationService.get_user_notifications(current_user.id)
    unread_count = NotificationService.get_unread_count(current_user.id)
    
    return render_template(
        'notifications/list.html',
        notifications=notifications,
        unread_count=unread_count
    )


@notifications_bp.route('/api/list')
@login_required
def api_notification_list():
    """API endpoint for notifications"""
    # Generate new notifications
    NotificationService.generate_all_notifications(current_user.id)
    
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    limit = request.args.get('limit', 20, type=int)
    
    notifications = NotificationService.get_user_notifications(
        current_user.id, 
        unread_only=unread_only,
        limit=limit
    )
    
    return jsonify({
        'success': True,
        'notifications': [n.to_dict() for n in notifications],
        'unread_count': NotificationService.get_unread_count(current_user.id)
    })


@notifications_bp.route('/api/unread-count')
@login_required
def api_unread_count():
    """Get unread notification count"""
    count = NotificationService.get_unread_count(current_user.id)
    return jsonify({'count': count})


@notifications_bp.route('/api/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def api_mark_read(notification_id):
    """Mark a notification as read"""
    success = NotificationService.mark_as_read(notification_id, current_user.id)
    return jsonify({
        'success': success,
        'unread_count': NotificationService.get_unread_count(current_user.id)
    })


@notifications_bp.route('/api/mark-all-read', methods=['POST'])
@login_required
def api_mark_all_read():
    """Mark all notifications as read"""
    NotificationService.mark_all_as_read(current_user.id)
    return jsonify({'success': True, 'unread_count': 0})


@notifications_bp.route('/api/dismiss/<int:notification_id>', methods=['POST'])
@login_required
def api_dismiss(notification_id):
    """Dismiss a notification"""
    success = NotificationService.dismiss_notification(notification_id, current_user.id)
    return jsonify({
        'success': success,
        'unread_count': NotificationService.get_unread_count(current_user.id)
    })


@notifications_bp.route('/settings')
@login_required
def notification_settings():
    """Notification settings page"""
    # Get or create preferences for all types
    preferences = {}
    for notif_type, defaults in DEFAULT_NOTIFICATION_SETTINGS.items():
        pref = NotificationService.get_user_preference(current_user.id, notif_type)
        preferences[notif_type] = {
            'label': defaults['label'],
            'is_enabled': pref.is_enabled,
            'email_enabled': pref.email_enabled,
            'sms_enabled': pref.sms_enabled,
            'push_enabled': pref.push_enabled,
            'days_before': pref.days_before,
            'default_days': defaults['days_before']
        }
    
    return render_template(
        'notifications/settings.html',
        preferences=preferences
    )


@notifications_bp.route('/settings/update', methods=['POST'])
@login_required
def update_settings():
    """Update notification settings"""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    for notif_type, settings in data.items():
        if notif_type not in DEFAULT_NOTIFICATION_SETTINGS:
            continue
        
        pref = NotificationPreference.query.filter_by(
            user_id=current_user.id,
            notification_type=notif_type
        ).first()
        
        if not pref:
            pref = NotificationPreference(
                user_id=current_user.id,
                notification_type=notif_type
            )
            db.session.add(pref)
        
        pref.is_enabled = settings.get('is_enabled', True)
        pref.email_enabled = settings.get('email_enabled', True)
        pref.sms_enabled = settings.get('sms_enabled', False)
        pref.push_enabled = settings.get('push_enabled', True)
        pref.days_before = settings.get('days_before', 1)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Settings updated successfully'})


@notifications_bp.route('/api/refresh', methods=['POST'])
@login_required
def api_refresh_notifications():
    """Manually refresh/regenerate notifications"""
    count = NotificationService.generate_all_notifications(current_user.id)
    return jsonify({
        'success': True,
        'new_notifications': count,
        'unread_count': NotificationService.get_unread_count(current_user.id)
    })