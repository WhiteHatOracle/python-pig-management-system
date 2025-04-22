from app import app, db  # Import your app and db from your actual app structure
from models import Litter, ServiceRecords

# Create an application context
with app.app_context():
    # Now you can interact with the database
    orphans = (
        Litter.query
        .outerjoin(ServiceRecords, Litter.service_record_id == ServiceRecords.id)
        .filter(ServiceRecords.id == None)
        .all()
    )

    # Delete orphaned records
    for orphan in orphans:
        db.session.delete(orphan)
    db.session.commit()

    print(f"Deleted {len(orphans)} orphaned litters.")
