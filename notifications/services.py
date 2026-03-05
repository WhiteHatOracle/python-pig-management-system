from datetime import date, datetime, timedelta, timezone
from sqlalchemy import and_, or_
from extensions import db
from models import User, Sows, ServiceRecords, Litter, VaccinationRecord
from notifications.models import Notification, NotificationPreference, DEFAULT_NOTIFICATION_SETTINGS


class NotificationService:
    """Service class to generate and manage notifications"""
    
    @staticmethod
    def get_user_preference(user_id, notification_type):
        """Get user preference for a notification type, create default if not exists"""
        pref = NotificationPreference.query.filter_by(
            user_id=user_id,
            notification_type=notification_type
        ).first()
        
        if not pref:
            defaults = DEFAULT_NOTIFICATION_SETTINGS.get(notification_type, {})
            pref = NotificationPreference(
                user_id=user_id,
                notification_type=notification_type,
                days_before=defaults.get('days_before', 1),
                is_enabled=True
            )
            db.session.add(pref)
            db.session.commit()
        
        return pref
    
    @staticmethod
    def create_notification(user_id, notification_type, title, message, 
                           scheduled_date, entity_type=None, entity_id=None,
                           priority=None):
        """Create a notification if it doesn't already exist"""
        
        # Check user preference
        pref = NotificationService.get_user_preference(user_id, notification_type)
        if not pref.is_enabled:
            return None
        
        # Calculate reminder date
        days_before = pref.days_before
        reminder_date = scheduled_date - timedelta(days=days_before)
        
        # Set priority
        if not priority:
            priority = DEFAULT_NOTIFICATION_SETTINGS.get(notification_type, {}).get('priority', 'normal')
        
        # Check if notification already exists
        existing = Notification.query.filter_by(
            user_id=user_id,
            notification_type=notification_type,
            entity_type=entity_type,
            entity_id=entity_id,
            scheduled_date=scheduled_date
        ).first()
        
        if existing:
            return existing
        
        # Create new notification
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            entity_type=entity_type,
            entity_id=entity_id,
            scheduled_date=scheduled_date,
            reminder_date=reminder_date
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return notification
    
    @staticmethod
    def generate_farrow_notifications(user_id):
        """Generate notifications for upcoming farrow dates"""
        today = date.today()
        future_limit = today + timedelta(days=30)  # Look 30 days ahead
        
        # Get all service records with due dates in range
        sows = Sows.query.filter_by(user_id=user_id).all()
        sow_ids = [s.id for s in sows]
        
        service_records = ServiceRecords.query.filter(
            ServiceRecords.sow_id.in_(sow_ids),
            ServiceRecords.due_date >= today,
            ServiceRecords.due_date <= future_limit
        ).all()
        
        notifications_created = 0
        
        for record in service_records:
            sow = next((s for s in sows if s.id == record.sow_id), None)
            if not sow:
                continue
            
            notification = NotificationService.create_notification(
                user_id=user_id,
                notification_type='farrow_due',
                title=f'Farrow Due: {sow.sowID}',
                message=f'Sow {sow.sowID} is due to farrow on {record.due_date.strftime("%B %d, %Y")}',
                scheduled_date=record.due_date,
                entity_type='service_record',
                entity_id=record.id
            )
            
            if notification:
                notifications_created += 1
        
        return notifications_created
    
    @staticmethod
    def generate_checkup_notifications(user_id):
        """Generate notifications for pregnancy checkups"""
        today = date.today()
        future_limit = today + timedelta(days=14)
        
        sows = Sows.query.filter_by(user_id=user_id).all()
        sow_ids = [s.id for s in sows]
        
        service_records = ServiceRecords.query.filter(
            ServiceRecords.sow_id.in_(sow_ids),
            ServiceRecords.checkup_date >= today,
            ServiceRecords.checkup_date <= future_limit
        ).all()
        
        notifications_created = 0
        
        for record in service_records:
            sow = next((s for s in sows if s.id == record.sow_id), None)
            if not sow:
                continue
            
            notification = NotificationService.create_notification(
                user_id=user_id,
                notification_type='checkup_due',
                title=f'Checkup Due: {sow.sowID}',
                message=f'Pregnancy checkup for {sow.sowID} scheduled for {record.checkup_date.strftime("%B %d, %Y")}',
                scheduled_date=record.checkup_date,
                entity_type='service_record',
                entity_id=record.id
            )
            
            if notification:
                notifications_created += 1
        
        return notifications_created
    
    @staticmethod
    def generate_litter_guard_notifications(user_id):
        """Generate notifications for litter guard vaccinations"""
        today = date.today()
        future_limit = today + timedelta(days=14)
        
        sows = Sows.query.filter_by(user_id=user_id).all()
        sow_ids = [s.id for s in sows]
        
        service_records = ServiceRecords.query.filter(
            ServiceRecords.sow_id.in_(sow_ids)
        ).filter(
            or_(
                and_(ServiceRecords.litter_guard1_date >= today, 
                     ServiceRecords.litter_guard1_date <= future_limit),
                and_(ServiceRecords.litter_guard2_date >= today, 
                     ServiceRecords.litter_guard2_date <= future_limit)
            )
        ).all()
        
        notifications_created = 0
        
        for record in service_records:
            sow = next((s for s in sows if s.id == record.sow_id), None)
            if not sow:
                continue
            
            # Check litter guard 1
            if record.litter_guard1_date and today <= record.litter_guard1_date <= future_limit:
                notification = NotificationService.create_notification(
                    user_id=user_id,
                    notification_type='litter_guard',
                    title=f'Litter Guard 1: {sow.sowID}',
                    message=f'First litter guard vaccination for {sow.sowID} on {record.litter_guard1_date.strftime("%B %d, %Y")}',
                    scheduled_date=record.litter_guard1_date,
                    entity_type='service_record',
                    entity_id=record.id
                )
                if notification:
                    notifications_created += 1
            
            # Check litter guard 2
            if record.litter_guard2_date and today <= record.litter_guard2_date <= future_limit:
                notification = NotificationService.create_notification(
                    user_id=user_id,
                    notification_type='litter_guard',
                    title=f'Litter Guard 2: {sow.sowID}',
                    message=f'Second litter guard vaccination for {sow.sowID} on {record.litter_guard2_date.strftime("%B %d, %Y")}',
                    scheduled_date=record.litter_guard2_date,
                    entity_type='service_record',
                    entity_id=record.id
                )
                if notification:
                    notifications_created += 1
        
        return notifications_created
    
    @staticmethod
    def generate_weaning_notifications(user_id):
        """Generate notifications for upcoming weaning dates"""
        today = date.today()
        future_limit = today + timedelta(days=14)
        
        sows = Sows.query.filter_by(user_id=user_id).all()
        sow_ids = [s.id for s in sows]
        
        litters = Litter.query.filter(
            Litter.sow_id.in_(sow_ids),
            Litter.wean_date >= today,
            Litter.wean_date <= future_limit
        ).all()
        
        notifications_created = 0
        
        for litter in litters:
            sow = next((s for s in sows if s.id == litter.sow_id), None)
            if not sow:
                continue
            
            notification = NotificationService.create_notification(
                user_id=user_id,
                notification_type='weaning_due',
                title=f'Weaning Due: Litter from {sow.sowID}',
                message=f'Litter from {sow.sowID} ({litter.current_alive} piglets) due for weaning on {litter.wean_date.strftime("%B %d, %Y")}',
                scheduled_date=litter.wean_date,
                entity_type='litter',
                entity_id=litter.id
            )
            
            if notification:
                notifications_created += 1
        
        return notifications_created
    
    @staticmethod
    def generate_vaccination_notifications(user_id):
        """Generate notifications for upcoming vaccinations"""
        today = date.today()
        future_limit = today + timedelta(days=14)
        
        sows = Sows.query.filter_by(user_id=user_id).all()
        sow_ids = [s.id for s in sows]
        
        litters = Litter.query.filter(Litter.sow_id.in_(sow_ids)).all()
        litter_ids = [l.id for l in litters]
        
        vaccinations = VaccinationRecord.query.filter(
            VaccinationRecord.litter_id.in_(litter_ids),
            VaccinationRecord.next_due_date >= today,
            VaccinationRecord.next_due_date <= future_limit
        ).all()
        
        notifications_created = 0
        
        for vacc in vaccinations:
            litter = next((l for l in litters if l.id == vacc.litter_id), None)
            if not litter:
                continue
            
            sow = next((s for s in sows if s.id == litter.sow_id), None)
            sow_id_str = sow.sowID if sow else f'Litter #{litter.id}'
            
            notification = NotificationService.create_notification(
                user_id=user_id,
                notification_type='vaccination_due',
                title=f'Vaccination Due: {vacc.vaccine_type}',
                message=f'{vacc.vaccine_type} vaccination for litter from {sow_id_str} due on {vacc.next_due_date.strftime("%B %d, %Y")}',
                scheduled_date=vacc.next_due_date,
                entity_type='vaccination_record',
                entity_id=vacc.id
            )
            
            if notification:
                notifications_created += 1
        
        return notifications_created
    
    @staticmethod
    def generate_all_notifications(user_id):
        """Generate all notification types for a user"""
        total = 0
        total += NotificationService.generate_farrow_notifications(user_id)
        total += NotificationService.generate_checkup_notifications(user_id)
        total += NotificationService.generate_litter_guard_notifications(user_id)
        total += NotificationService.generate_weaning_notifications(user_id)
        total += NotificationService.generate_vaccination_notifications(user_id)
        return total
    
    @staticmethod
    def get_user_notifications(user_id, unread_only=False, limit=50):
        """Get notifications for a user"""
        query = Notification.query.filter_by(
            user_id=user_id,
            is_dismissed=False
        )
        
        if unread_only:
            query = query.filter_by(is_read=False)
        
        return query.order_by(
            Notification.scheduled_date.asc(),
            Notification.priority.desc()
        ).limit(limit).all()
    
    @staticmethod
    def get_today_notifications(user_id):
        """Get notifications due today or overdue"""
        today = date.today()
        return Notification.query.filter(
            Notification.user_id == user_id,
            Notification.is_dismissed == False,
            Notification.reminder_date <= today
        ).order_by(
            Notification.scheduled_date.asc()
        ).all()
    
    @staticmethod
    def get_unread_count(user_id):
        """Get count of unread notifications"""
        today = date.today()
        return Notification.query.filter(
            Notification.user_id == user_id,
            Notification.is_read == False,
            Notification.is_dismissed == False,
            Notification.reminder_date <= today
        ).count()
    
    @staticmethod
    def mark_as_read(notification_id, user_id):
        """Mark a notification as read"""
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=user_id
        ).first()
        
        if notification:
            notification.mark_as_read()
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def mark_all_as_read(user_id):
        """Mark all notifications as read for a user"""
        Notification.query.filter_by(
            user_id=user_id,
            is_read=False
        ).update({'is_read': True, 'read_at': datetime.now(timezone.utc)})
        db.session.commit()
    
    @staticmethod
    def dismiss_notification(notification_id, user_id):
        """Dismiss a notification"""
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=user_id
        ).first()
        
        if notification:
            notification.is_dismissed = True
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def cleanup_old_notifications(days=90):
        """Remove old dismissed and read notifications"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        deleted = Notification.query.filter(
            Notification.is_dismissed == True,
            Notification.created_at < cutoff
        ).delete()
        
        db.session.commit()
        return deleted