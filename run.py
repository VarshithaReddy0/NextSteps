import os
from app import create_app, db
from app.models import Admin

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

# ------------------ ADD THIS ------------------
@app.after_request
def add_csp(response):
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' https://www.googletagmanager.com https://www.google-analytics.com; "
        "connect-src 'self' https://www.google-analytics.com; "
        "img-src 'self' https://www.google-analytics.com data:; "
        "style-src 'self' 'unsafe-inline';"
    )
    return response
# ------------------ END OF CSP ----------------

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
