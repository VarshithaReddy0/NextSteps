from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

# Association Table for Job-Batches Many-to-Many Relationship
job_batches = db.Table(
    'job_batches',
    db.Column('job_id', db.Integer, db.ForeignKey('job.id')),
    db.Column('batch_id', db.Integer, db.ForeignKey('batch.id'))
)

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


class Batch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<Batch {self.name}>'


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    apply_link = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(200))
    min_experience = db.Column(db.Integer)
    max_experience = db.Column(db.Integer)  # NEW FIELD
    package_min = db.Column(db.Float)
    package_max = db.Column(db.Float)
    posted_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    batches = db.relationship('Batch', secondary=job_batches, backref='jobs')

    @property
    def package_range(self):
        if self.package_min and self.package_max:
            return f"₹{self.package_min:.2f} - ₹{self.package_max:.2f} LPA"
        return "Not specified"

    def __repr__(self):
        return f'<Job {self.title} at {self.company}>'