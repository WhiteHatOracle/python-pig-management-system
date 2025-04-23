from app import db, app
from sqlalchemy import text
with app.app_context():
     db.session.execute(text("DROP TABLE IF EXISTS alembic_version"))