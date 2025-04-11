from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

# Initialize the database
db = SQLAlchemy()

# Define User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True, index=True)
    password = db.Column(db.String(80), nullable=False)

# Define the Boar model
class Boars(db.Model):
    __tablename__ = "boars"
    id = db.Column(db.Integer, primary_key=True)
    BoarId = db.Column(db.String(20), nullable=False, unique=True, index=True)
    Breed = db.Column(db.String(50), nullable=False, index=True)
    DOB = db.Column(db.Date)

# Define the Sows model
class Sows(db.Model):
    __tablename__ = "sows"
    id = db.Column(db.Integer, primary_key=True)
    sowID = db.Column(db.String(20), nullable=False, unique=True, index=True)
    Breed = db.Column(db.String(50), nullable=False, unique=True, index=True, server_default='UNKNOWN')
    DOB = db.Column(db.Date)
    service_records = db.relationship("ServiceRecords", back_populates="sow", cascade="all, delete-orphan")

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

    Litter_records = db.relationship('Litter', backref='service_record', lazy=True)
    sow = db.relationship("Sows", back_populates="service_records")

class Invoice(db.Model):
    __tablename__ = "Invoice"
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    company_name = db.Column(db.String(255), nullable=False)
    num_of_pigs = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, default=lambda: datetime.now(timezone.utc), nullable=False)
    total_weight = db.Column(db.Float, nullable=False)
    average_weight = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<Invoice {self.invoice_number}>"

class Expense(db.Model):
    __tablename__="Expense"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    vendor = db.Column(db.String(100))
    description = db.Column(db.String(200))

    def __repr__(self):
        return f'<Expense {self.id} - {self.category}>'
    
class Litter(db.Model):
    __tablename__="Litter"
    id = db.Column(db.Integer, primary_key=True)
    service_record_id = db.Column(db.Integer, db.ForeignKey('service_records.id'), nullable=False)
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