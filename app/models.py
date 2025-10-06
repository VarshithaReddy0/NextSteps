from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Admin {self.username}>'


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    batch = db.Column(db.String(50), nullable=False)  # 2024, 2025, 2026
    experience_level = db.Column(db.String(50), nullable=False)  # Fresher, SDE-1, SDE-2
    package_min = db.Column(db.Float, nullable=False)
    package_max = db.Column(db.Float, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    skills_required = db.Column(db.String(500), nullable=False)
    apply_link = db.Column(db.String(500), nullable=False)
    posted_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    @property
    def package_range(self):
        return f"₹{self.package_min}-{self.package_max} LPA"

    def __repr__(self):
        return f'<Job {self.title} at {self.company}>'