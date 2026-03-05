from datetime import datetime, timezone
from extensions import db


class Notification(db.Model):
    """Store individual notifications for users"""
    __tablename__ = 'notification'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    
    # Notification content
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    # Type and categorization
    notification_type = db.Column(db.String(50), nullable=False, index=True)
    # Types: farrow_due, vaccination_due, checkup_due, weaning_due, 
    #        litter_guard, feed_up, iron_injection, castration, health_alert, system
    
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, urgent
    
    # Related entity (for linking to specific records)
    entity_type = db.Column(db.String(50))  # sow, litter, service_record, vaccination
    entity_id = db.Column(db.Integer)
    
    # Scheduling
    scheduled_date = db.Column(db.Date, nullable=False, index=True)  # When event happens
    reminder_date = db.Column(db.Date, nullable=False, index=True)   # When to notify
    
    # Status
    is_read = db.Column(db.Boolean, default=False, index=True)
    is_dismissed = db.Column(db.Boolean, default=False)
    is_sent_email = db.Column(db.Boolean, default=False)
    is_sent_sms = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    read_at = db.Column(db.DateTime(timezone=True))
    
    # Relationships
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic', cascade='all, delete-orphan'))
    
    # Prevent duplicate notifications
    __table_args__ = (
        db.UniqueConstraint('user_id', 'notification_type', 'entity_type', 'entity_id', 'scheduled_date', 
                           name='uix_unique_notification'),
    )
    
    @property
    def is_overdue(self):
        """Check if the scheduled event date has passed"""
        from datetime import date
        return self.scheduled_date < date.today()
    
    @property
    def days_until(self):
        """Days until the scheduled event"""
        from datetime import date
        delta = self.scheduled_date - date.today()
        return delta.days
    
    @property
    def icon(self):
        """Return appropriate icon for notification type"""
        icons = {
            'farrow_due': 'fa-piggy-bank',
            'vaccination_due': 'fa-syringe',
            'checkup_due': 'fa-stethoscope',
            'weaning_due': 'fa-baby',
            'litter_guard': 'fa-shield-alt',
            'feed_up': 'fa-wheat-awn',
            'iron_injection': 'fa-vial',
            'castration': 'fa-cut',
            'health_alert': 'fa-heart-pulse',
            'system': 'fa-bell',
        }
        return icons.get(self.notification_type, 'fa-bell')
    
    @property
    def color(self):
        """Return color class based on priority/type"""
        if self.is_overdue:
            return 'danger'
        
        colors = {
            'urgent': 'danger',
            'high': 'warning',
            'normal': 'primary',
            'low': 'secondary',
        }
        return colors.get(self.priority, 'primary')
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.now(timezone.utc)
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'type': self.notification_type,
            'priority': self.priority,
            'scheduled_date': self.scheduled_date.isoformat() if self.scheduled_date else None,
            'days_until': self.days_until,
            'is_overdue': self.is_overdue,
            'is_read': self.is_read,
            'icon': self.icon,
            'color': self.color,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self):
        return f'<Notification {self.id} - {self.notification_type} for User {self.user_id}>'


class NotificationPreference(db.Model):
    """User preferences for each notification type"""
    __tablename__ = 'notification_preference'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    
    notification_type = db.Column(db.String(50), nullable=False)
    
    # Enable/disable
    is_enabled = db.Column(db.Boolean, default=True)
    
    # Delivery channels
    email_enabled = db.Column(db.Boolean, default=True)
    sms_enabled = db.Column(db.Boolean, default=False)
    push_enabled = db.Column(db.Boolean, default=True)
    
    # Timing (days before event to send reminder)
    days_before = db.Column(db.Integer, default=1)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('notification_preferences', lazy='dynamic'))
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'notification_type', name='uix_user_notification_type'),
    )
    
    def __repr__(self):
        return f'<NotificationPreference {self.notification_type} for User {self.user_id}>'


# Default notification settings
DEFAULT_NOTIFICATION_SETTINGS = {
    'farrow_due': {'days_before': 3, 'priority': 'high', 'label': 'Farrow Due Date'},
    'vaccination_due': {'days_before': 1, 'priority': 'high', 'label': 'Vaccination Due'},
    'checkup_due': {'days_before': 1, 'priority': 'normal', 'label': 'Pregnancy Checkup'},
    'weaning_due': {'days_before': 3, 'priority': 'normal', 'label': 'Weaning Due'},
    'litter_guard': {'days_before': 1, 'priority': 'normal', 'label': 'Litter Guard Vaccination'},
    'feed_up': {'days_before': 1, 'priority': 'low', 'label': 'Feed Increase'},
    'iron_injection': {'days_before': 0, 'priority': 'normal', 'label': 'Iron Injection'},
    'castration': {'days_before': 1, 'priority': 'normal', 'label': 'Castration Due'},
    'health_alert': {'days_before': 0, 'priority': 'urgent', 'label': 'Health Alert'},
    'system': {'days_before': 0, 'priority': 'low', 'label': 'System Notifications'},
}