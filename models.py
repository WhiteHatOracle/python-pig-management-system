from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_admin.contrib.sqla import ModelView
from extensions import db, admin

# Define User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)  # usually email
    email = db.Column(db.String(200), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=True)
    verification_token = db.Column(db.String(200), nullable=True)
    verification_expiry = db.Column(db.DateTime(timezone=True), nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    password_reset_token = db.Column(db.String(128), nullable=True)
    password_reset_expiry = db.Column(db.DateTime, nullable=True)

    # Fields for Google login
    google_id = db.Column(db.String(255), unique=True, nullable=True)
    name = db.Column(db.String(255), nullable=True)
    profile_pic = db.Column(db.String(512), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships for ownership
    boars = db.relationship("Boars", back_populates="owner", cascade="all, delete-orphan", passive_deletes=True)
    sows = db.relationship("Sows", back_populates="owner", cascade="all, delete-orphan", passive_deletes=True)
    invoices = db.relationship("Invoice", back_populates="owner", cascade="all, delete-orphan", passive_deletes=True)
    expenses = db.relationship("Expense", back_populates="owner", cascade="all, delete-orphan", passive_deletes=True)


# Define the Boar model
class Boars(db.Model):
    __tablename__ = "boars"
    id = db.Column(db.Integer, primary_key=True)
    BoarId = db.Column(db.String(20), nullable=False, index=True)
    Breed = db.Column(db.String(50), nullable=False, index=True)
    DOB = db.Column(db.Date)

    # Link to owner
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    owner = db.relationship("User", back_populates="boars")

    __table_args__ = (
        db.UniqueConstraint('BoarId', 'user_id', name='uix_boarid_userid'),
    )


# Define the Sows model
class Sows(db.Model):
    __tablename__ = "sows"
    id = db.Column(db.Integer, primary_key=True)
    sowID = db.Column(db.String(20), nullable=False, index=True)
    Breed = db.Column(db.String(50), nullable=False, unique=False, index=True, server_default='UNKNOWN')
    DOB = db.Column(db.Date)

    # Service records (cascades via ORM + DB)    
    service_records = db.relationship(
        "ServiceRecords", 
        back_populates="sow", 
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    # Litters relationship
    litters = db.relationship(
        "Litter",
        back_populates="sow",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    # Link to owner
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    owner = db.relationship("User", back_populates="sows")

    __table_args__ = (
        db.UniqueConstraint('sowID', 'user_id', name='uix_sowid_userid'),
    )


# Define the Service Records
class ServiceRecords(db.Model):
    __tablename__ = "service_records"
    id = db.Column(db.Integer, primary_key=True)
    sow_id = db.Column(db.Integer, db.ForeignKey("sows.id", ondelete="CASCADE"), nullable=False)
    service_date = db.Column(db.Date)
    boar_used = db.Column(db.String(50), nullable=False)

    checkup_date = db.Column(db.Date)
    litter_guard1_date = db.Column(db.Date)
    litter_guard2_date = db.Column(db.Date)
    feed_up_date = db.Column(db.Date)
    due_date = db.Column(db.Date)
    action_date = db.Column(db.Date)

    # Relationship to litter
    litter = db.relationship(
        'Litter',
        back_populates='service_record',
        uselist=False,
        cascade='all, delete-orphan',
        passive_deletes=True
    )
    
    sow = db.relationship("Sows", back_populates="service_records")

    __table_args__ = (
        db.UniqueConstraint('sow_id', 'service_date', name='uix_sow_service_date'),
    )

    
class Invoice(db.Model):
    __tablename__ = "invoice"
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), nullable=False)
    company_name = db.Column(db.String(255), nullable=False)
    num_of_pigs = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, default=lambda: datetime.now(timezone.utc), nullable=False)
    total_weight = db.Column(db.Float, nullable=False)
    average_weight = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)

    # Link to owner
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    owner = db.relationship("User", back_populates="invoices")

    __table_args__ = (
        db.UniqueConstraint('invoice_number', 'user_id', name='uix_invoiceid_userid'),
    )

    def __repr__(self):
        return f"<Invoice {self.invoice_number}>"


# Define the Expense model    
class Expense(db.Model):
    __tablename__ = "expense"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    invoice_number = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    vendor = db.Column(db.String(100))
    description = db.Column(db.String(200))

    # Link to owner
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    owner = db.relationship("User", back_populates="expenses")

    __table_args__ = (
        db.UniqueConstraint('user_id', 'invoice_number', name='uix_user_receipt'),
    )

    def __repr__(self):
        return f'<Expense {self.id} - {self.category}>'


# ==================== LITTER AND RELATED MODELS ====================
# In models.py - Update the Litter class

class Litter(db.Model):
    __tablename__ = 'litter'
    
    id = db.Column(db.Integer, primary_key=True)
    sow_id = db.Column(db.Integer, db.ForeignKey('sows.id', ondelete='CASCADE'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service_records.id', ondelete='CASCADE'), nullable=False)
    
    # Birth data
    farrowDate = db.Column(db.Date, nullable=False)
    totalBorn = db.Column(db.Integer, nullable=False)
    bornAlive = db.Column(db.Integer, nullable=False)
    stillBorn = db.Column(db.Integer, default=0)
    mummified = db.Column(db.Integer, default=0)
    averageWeight = db.Column(db.Float)
    weights = db.Column(db.String(500))
    
    # Early life procedures
    iron_injection_date = db.Column(db.Date)
    teeth_clipping_date = db.Column(db.Date)
    tail_docking_date = db.Column(db.Date)
    castration_date = db.Column(db.Date)
    wean_date = db.Column(db.Date)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    sow = db.relationship("Sows", back_populates="litters")
    service_record = db.relationship("ServiceRecords", back_populates="litter")
    management_records = db.relationship('LitterManagement', back_populates='litter', lazy=True, cascade='all, delete-orphan', passive_deletes=True)
    vaccination_records = db.relationship('VaccinationRecord', back_populates='litter', lazy=True, cascade='all, delete-orphan', passive_deletes=True)
    weight_records = db.relationship('WeightRecord', back_populates='litter', lazy=True, cascade='all, delete-orphan', passive_deletes=True)
    mortality_records = db.relationship('MortalityRecord', back_populates='litter', lazy=True, cascade='all, delete-orphan', passive_deletes=True)
    sale_records = db.relationship('SaleRecord', back_populates='litter', lazy=True, cascade='all, delete-orphan', passive_deletes=True)
    
    @property
    def total_mortalities(self):
        """Total number of piglets that died"""
        return sum(m.number_died for m in self.mortality_records)
    
    @property
    def total_sold(self):
        """Total number of piglets sold"""
        return sum(s.number_sold for s in self.sale_records)
    
    @property
    def total_fostered_in(self):
        """Total piglets received from other litters"""
        return sum(
            m.piglets_moved or 0 
            for m in self.management_records 
            if m.management_type == 'cross_foster_in'
        )
    
    @property
    def total_fostered_out(self):
        """Total piglets given to other litters"""
        return sum(
            m.piglets_moved or 0 
            for m in self.management_records 
            if m.management_type == 'cross_foster_out'
        )
    
    @property
    def current_alive(self):
        """Calculate currently alive piglets"""
        alive = self.bornAlive or 0
        alive += self.total_fostered_in
        alive -= self.total_fostered_out
        alive -= self.total_mortalities
        alive -= self.total_sold
        return max(0, alive)
    
    @property
    def age_days(self):
        """Calculate age in days from farrow date"""
        if self.farrowDate:
            from datetime import date
            return (date.today() - self.farrowDate).days
        return 0
    
    @property
    def stage(self):
        """Determine current growth stage based on age"""
        age = self.age_days
        
        if age < 0:
            return 'unknown'
        elif age <= 21:
            return 'preweaning'
        elif age <= 56:
            return 'weaner'
        elif age <= 98:
            return 'grower'
        else:
            return 'finisher'
    
    @property
    def survival_rate(self):
        """Calculate survival rate as percentage"""
        initial = self.bornAlive + self.total_fostered_in
        if initial == 0:
            return 0
        return round((self.current_alive / initial) * 100, 1)
    
    @property
    def latest_avg_weight(self):
        """Get the most recent average weight"""
        if self.weight_records:
            latest = max(self.weight_records, key=lambda x: x.date)
            return latest.average_weight
        return None
    
    def __repr__(self):
        return f'<Litter {self.id} - Sow {self.sow_id} - {self.current_alive} alive>'
    
class LitterManagement(db.Model):
    __tablename__ = 'litter_management'
    
    id = db.Column(db.Integer, primary_key=True)
    litter_id = db.Column(db.Integer, db.ForeignKey('litter.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    management_type = db.Column(db.String(50), nullable=False)  # single, cross_foster_in, cross_foster_out, combined
    other_litter_id = db.Column(db.String(50))  # ID of other sow/litter involved
    piglets_moved = db.Column(db.Integer)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationship back to litter
    litter = db.relationship('Litter', back_populates='management_records')

    def __repr__(self):
        return f'<LitterManagement {self.id} - {self.management_type}>'


class VaccinationRecord(db.Model):
    __tablename__ = 'vaccination_record'
    
    id = db.Column(db.Integer, primary_key=True)
    litter_id = db.Column(db.Integer, db.ForeignKey('litter.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    vaccine_type = db.Column(db.String(100), nullable=False)
    other_vaccine_name = db.Column(db.String(100))
    piglets_vaccinated = db.Column(db.Integer, nullable=False)
    dosage = db.Column(db.Float)
    next_due_date = db.Column(db.Date)
    administered_by = db.Column(db.String(100))
    batch_number = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationship back to litter
    litter = db.relationship('Litter', back_populates='vaccination_records')

    def __repr__(self):
        return f'<VaccinationRecord {self.id} - {self.vaccine_type}>'


class WeightRecord(db.Model):
    __tablename__ = 'weight_record'
    
    id = db.Column(db.Integer, primary_key=True)
    litter_id = db.Column(db.Integer, db.ForeignKey('litter.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    weight_type = db.Column(db.String(20), default='average')  # average, individual, sample
    piglets_weighed = db.Column(db.Integer)
    average_weight = db.Column(db.Float, nullable=False)
    individual_weights = db.Column(db.Text)  # Comma-separated weights
    total_weight = db.Column(db.Float)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationship back to litter
    litter = db.relationship('Litter', back_populates='weight_records')
    
    @property
    def age_days(self):
        """Calculate age at time of weighing"""
        if self.litter and self.litter.farrowDate:
            return (self.date - self.litter.farrowDate).days
        return None
    
    @property
    def daily_gain(self):
        """Calculate daily gain compared to previous weight record"""
        if not self.litter or not self.litter.weight_records:
            return None
        
        sorted_records = sorted(self.litter.weight_records, key=lambda x: x.date)
        try:
            idx = sorted_records.index(self)
        except ValueError:
            return None
        
        if idx == 0:
            # Compare to birth weight
            if self.litter.averageWeight and self.age_days and self.age_days > 0:
                return round((self.average_weight - self.litter.averageWeight) / self.age_days, 2)
            return None
        
        prev_record = sorted_records[idx - 1]
        days_diff = (self.date - prev_record.date).days
        if days_diff > 0:
            return round((self.average_weight - prev_record.average_weight) / days_diff, 2)
        return None

    def __repr__(self):
        return f'<WeightRecord {self.id} - {self.average_weight}kg>'


class MortalityRecord(db.Model):
    __tablename__ = 'mortality_record'
    
    id = db.Column(db.Integer, primary_key=True)
    litter_id = db.Column(db.Integer, db.ForeignKey('litter.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    number_died = db.Column(db.Integer, nullable=False)
    cause = db.Column(db.String(50), nullable=False)
    other_cause = db.Column(db.String(200))
    age_at_death = db.Column(db.Integer)  # days
    weight_at_death = db.Column(db.Float)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationship back to litter
    litter = db.relationship('Litter', back_populates='mortality_records')

    def __repr__(self):
        return f'<MortalityRecord {self.id} - {self.number_died} died>'


class SaleRecord(db.Model):
    __tablename__ = 'sale_record'
    
    id = db.Column(db.Integer, primary_key=True)
    litter_id = db.Column(db.Integer, db.ForeignKey('litter.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    number_sold = db.Column(db.Integer, nullable=False)
    average_weight = db.Column(db.Float, nullable=False)
    total_weight = db.Column(db.Float)
    price_per_kg = db.Column(db.Float)
    total_amount = db.Column(db.Float)
    buyer_name = db.Column(db.String(100))
    buyer_contact = db.Column(db.String(100))
    sale_type = db.Column(db.String(20), default='market')  # market, breeding, weaner, culled
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationship back to litter
    litter = db.relationship('Litter', back_populates='sale_records')

    def __repr__(self):
        return f'<SaleRecord {self.id} - {self.number_sold} sold>'