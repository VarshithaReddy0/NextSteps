from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect  # ADD THIS
from app.config import config

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()  # ADD THIS

@login_manager.user_loader
def load_user(user_id):
    from app.models import Admin
    return Admin.query.get(int(user_id))

def create_app(config_name='default'):
    import os
    template_dir = os.path.abspath('templates')
    app = Flask(__name__, template_folder=template_dir)
    app.config.from_object(config[config_name])

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)  # ADD THIS

    login_manager.login_view = 'admin.login'
    login_manager.login_message = 'Please log in to access the admin panel.'

    # ADD ERROR HANDLERS (NEW)
    @app.errorhandler(404)
    def not_found(error):
        return "Page not found", 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return "Internal server error", 500

    with app.app_context():
        from app import models

    from app.routes import main, admin
    app.register_blueprint(main.bp)
    app.register_blueprint(admin.bp)

    return app