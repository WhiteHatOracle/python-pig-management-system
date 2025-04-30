from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

# Initialize the database
db = SQLAlchemy()

# Define User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)  # usually email
    password = db.Column(db.String(255), nullable=True)

    # NEW FIELDS for Google login
    google_id = db.Column(db.String(255), unique=True, nullable=True)
    name = db.Column(db.String(255), nullable=True)
    profile_pic = db.Column(db.String(512), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships for ownership
    boars = db.relationship("Boars", back_populates="owner", cascade="all, delete-orphan")
    sows = db.relationship("Sows", back_populates="owner", cascade="all, delete-orphan")
    invoices = db.relationship("Invoice", back_populates="owner", cascade="all, delete-orphan")
    expenses = db.relationship("Expense", back_populates="owner", cascade="all, delete-orphan")


# Define the Boar model
class Boars(db.Model):
    __tablename__ = "boars"
    id = db.Column(db.Integer, primary_key=True)
    BoarId = db.Column(db.String(20), nullable=False, index=True)
    Breed = db.Column(db.String(50), nullable=False, index=True)
    DOB = db.Column(db.Date)

    # Link to owner
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
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
    service_records = db.relationship("ServiceRecords", back_populates="sow", cascade="all, delete-orphan")

    # Link to owner
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    owner = db.relationship("User", back_populates="sows")

    __table_args__ = (
        db.UniqueConstraint('sowID', 'user_id', name='uix_sowid_userid'),
    )

# Define the Service Records
class ServiceRecords(db.Model):
    __tablename__ = "service_records"
    id = db.Column(db.Integer, primary_key=True)
    sow_id = db.Column(db.Integer, db.ForeignKey("sows.id"), nullable=False)
    service_date = db.Column(db.Date, nullable=False)
    boar_used = db.Column(db.String(50), nullable=False)

    checkup_date = db.Column(db.Date)
    litter_guard1_date = db.Column(db.Date)
    litter_guard2_date = db.Column(db.Date)
    feed_up_date = db.Column(db.Date)
    due_date = db.Column(db.Date)
    action_date = db.Column(db.Date)

    litter = db.relationship('Litter', backref='service_record', uselist=False, passive_deletes=True)
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
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
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
    invoice_number = db.Column(db.String(100),nullable=False)
    category = db.Column(db.String(50), nullable=False)
    vendor = db.Column(db.String(100))
    description = db.Column(db.String(200))

    # Link to owner
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    owner = db.relationship("User", back_populates="expenses")

    __table_args__ = (
        db.UniqueConstraint('user_id', 'invoice_number', name='uix_user_receipt'),  # Optional constraint
    )

    def __repr__(self):
        return f'<Expense {self.id} - {self.category}>'


class Litter(db.Model):
    __tablename__="litter"
    id = db.Column(db.Integer, primary_key=True)
    service_record_id = db.Column(db.Integer, db.ForeignKey('service_records.id', ondelete='CASCADE', name='fk_service_record_id'), nullable=False)
    farrowDate = db.Column(db.Date, nullable=False)
    totalBorn = db.Column(db.Integer, nullable=False)
    stillBorn = db.Column(db.Integer,nullable=False)
    bornAlive = db.Column(db.Integer, nullable=False)
    
    iron_injection_date = db.Column(db.Date, nullable=False)
    tail_dorking_date = db.Column(db.Date, nullable=False)
    teeth_clipping_date = db.Column(db.Date, nullable=False)
    castration_date = db.Column(db.Date, nullable=False)
    wean_date = db.Column(db.Date, nullable=False)
    averageWeight = db.Column(db.Float)

    sow_id = db.Column(db.Integer, db.ForeignKey('sows.id'))
    sow = db.relationship('Sows', backref='litters')
