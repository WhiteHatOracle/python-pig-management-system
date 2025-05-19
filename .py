# from app import db, app
# from sqlalchemy import text

# with app.app_context():
#     with db.engine.connect() as conn:
#         result = conn.execute(text("PRAGMA table_info(user)"))
#         print(result.fetchall())


from app import db, app
from models import User  # or adjust path if needed

with app.app_context():
     user = User.query.filter_by(email="danieltphiri9@gmail.com").first()
     if user:
          db.session.delete(user)
          db.session.commit()
          print("User deleted.")
     else:
          print("User not found.") 