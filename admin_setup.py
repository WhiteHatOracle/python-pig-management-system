# admin_setup.py
from flask_admin.contrib.sqla import ModelView
from extensions import admin, db
from models import User, Boars, Sows, ServiceRecords, Invoice, Expense, Litter


def setup_admin_views():
    """Register all admin views - call this AFTER app initialization"""
    admin.add_view(ModelView(User, db.session, category="Users"))
    admin.add_view(ModelView(Boars, db.session, category="Pigs"))
    admin.add_view(ModelView(Sows, db.session, category="Pigs"))
    admin.add_view(ModelView(ServiceRecords, db.session, category="Records"))
    admin.add_view(ModelView(Invoice, db.session, category="Finance"))
    admin.add_view(ModelView(Expense, db.session, category="Finance"))
    admin.add_view(ModelView(Litter, db.session, category="Records"))