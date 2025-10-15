from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

# Association Table for Job-Batches Many-to-Many Relationship
job_batches = db.Table(
    'job_batches',
    db.Column('job_id', db.Integer, db.ForeignKey('job.id'), primary_key=True),
    db.Column('batch_id', db.Integer, db.ForeignKey('batch.id'), primary_key=True)
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
    company_name = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    apply_link = db.Column(db.String(500), nullable=False)

    # Job type flags
    is_internship = db.Column(db.Boolean, default=False)
    is_hackathon = db.Column(db.Boolean, default=False)

    # Compensation fields
    salary = db.Column(db.Numeric(10, 2), nullable=True)
    stipend = db.Column(db.Numeric(10, 2), nullable=True)
    prize_money = db.Column(db.Numeric(10, 2), nullable=True)

    # Hackathon specific
    deadline = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Relationship with Batch
    batches = db.relationship('Batch', secondary=job_batches, backref='jobs')

    @property
    def salary_display(self):
        if self.salary:
            return f"₹{int(self.salary):,} LPA"
        return None

    @property
    def stipend_display(self):
        if self.stipend:
            return f"₹{int(self.stipend):,}/month"
        return None

    @property
    def prize_display(self):
        if self.prize_money:
            return f"₹{int(self.prize_money):,}"
        return None

    @property
    def is_new(self):
        return (datetime.utcnow() - self.created_at).days <= 7

    @property
    def job_type(self):
        if self.is_hackathon:
            return "Hackathon"
        elif self.is_internship:
            return "Internship"
        else:
            return "Full Time"

    @property
    def batch_names(self):
        return ', '.join([batch.name for batch in self.batches])

    def __repr__(self):
        return f'<Job {self.role} at {self.company_name}>'


# ==================== PUSH NOTIFICATION MODEL ====================
class PushSubscription(db.Model):
    __tablename__ = 'push_subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    endpoint = db.Column(db.String(500), unique=True, nullable=False, index=True)
    batch = db.Column(db.String(10), nullable=False, index=True)
    subscription_json = db.Column(db.Text)
    user_agent = db.Column(db.String(200))
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_notified = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True, index=True)

    def __repr__(self):
        return f'<PushSubscription {self.batch} - {self.endpoint[:30]}...>'