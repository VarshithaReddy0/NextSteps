import os
from app import create_app, db
from app.models import Admin

app = create_app(os.getenv('FLASK_CONFIG') or 'default')


def init_admin():
    """Create default admin if not exists"""
    with app.app_context():
        admin = Admin.query.filter_by(username='admin').first()
        if not admin:
            admin = Admin(username='admin')
            admin.set_password('admin123')  # Change this in production!
            db.session.add(admin)
            db.session.commit()
            print("✅ Default admin created (username: admin, password: admin123)")


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_admin()
    app.run(debug=True)