# extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_login import LoginManager
from flask_migrate import Migrate

# Initialize extensions (without app)
db = SQLAlchemy()
admin = Admin(name="Pig Management Admin")
login_manager = LoginManager()
migrate = Migrate()