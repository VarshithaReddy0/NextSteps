import os
from app import create_app, db
from app.models import Admin

app = create_app(os.getenv('FLASK_CONFIG') or 'production')

with app.app_context():
    admin = Admin.query.filter_by(username=os.getenv('ADMIN_USERNAME', 'admin')).first()

    if not admin:
        admin = Admin(username=os.getenv('ADMIN_USERNAME', 'admin'))
        admin.set_password(os.getenv('ADMIN_PASSWORD', 'admin123'))
        db.session.add(admin)
        db.session.commit()
        print(f"✓ Admin created: {admin.username}")
    else:
        print(f"✓ Admin exists: {admin.username}")