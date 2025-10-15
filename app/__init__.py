from flask import Flask, request, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
import logging
import os
from app.config import config

# Initialize Flask extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()

@login_manager.user_loader
def load_user(user_id):
    from app.models import Admin
    return Admin.query.get(int(user_id))


def create_app(config_name='default'):
    template_dir = os.path.abspath('templates')
    static_dir = os.path.abspath('static')

    # Flask app instance
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Login manager setup
    login_manager.login_view = 'admin.login'
    login_manager.login_message = 'Please log in to access the admin panel.'

    # Exempt API routes from CSRF validation
    @app.before_request
    def exempt_routes_from_csrf():
        exempt_routes = app.config.get('WTF_CSRF_EXEMPT_ROUTES', [])
        if request.path in exempt_routes:
            setattr(request, '_csrf_exempt', True)

    # Security headers
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://plausible.io https://www.googletagmanager.com https://www.google-analytics.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "font-src 'self' https://cdn.jsdelivr.net data:; "
            "img-src 'self' data: blob: https:; "
            "connect-src 'self' https://cdn.jsdelivr.net https://plausible.io https://www.google-analytics.com; "
            "object-src 'none'; "
            "base-uri 'self';"
        )
        return response

    # ==================== NEW: SERVICE WORKER ROUTE ====================
    @app.route('/sw.js')
    def service_worker():
        """Serve service worker from root path (required for scope)"""
        return send_from_directory(
            os.path.join(app.static_folder, 'js'),
            'sw.js',
            mimetype='application/javascript'
        )

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403

    # Blueprint registration
    from app.routes import main, admin
    from app.routes.notifications import notifications_bp
    app.register_blueprint(main.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(notifications_bp)

    # Logging setup
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = logging.FileHandler('logs/flask.log')
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.info('Flask application startup.')

    return app