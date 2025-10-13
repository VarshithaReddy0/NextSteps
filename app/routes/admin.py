from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import Admin, Job, Batch
from datetime import datetime
import re

bp = Blueprint('admin', __name__, url_prefix='/admin')


# ==================== HELPER FUNCTIONS ====================

def validate_url(url):
    """Validate URL format"""
    if not url:
        return False
    url_pattern = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None


def sanitize_input(text, max_length=500):
    """Basic input sanitization"""
    if not text:
        return text
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<[^>]+>', '', text)
    return text[:max_length].strip()


def validate_number(value, field_name, min_val=0, max_val=None):
    """Validate numeric input"""
    if not value:
        return None
    try:
        num = float(value)
        if num < min_val:
            flash(f"{field_name} cannot be negative.", "danger")
            return None
        if max_val and num > max_val:
            flash(f"{field_name} cannot exceed {max_val}.", "danger")
            return None
        return num
    except ValueError:
        flash(f"Invalid {field_name}. Please enter a valid number.", "danger")
        return None


def process_batches(batch_input, job):
    """
    Helper function to process batch names correctly.
    Splits comma-separated values and creates individual batch records.
    """
    if not batch_input:
        return

    batch_names = [name.strip() for name in batch_input.split(',') if name.strip()]

    for name in batch_names:
        name = sanitize_input(name, 10)

        if ',' in name:
            flash(f"Invalid batch name: {name}. Please enter single years only.", "warning")
            continue

        batch = Batch.query.filter_by(name=name).first()
        if not batch:
            batch = Batch(name=name)
            db.session.add(batch)
            db.session.flush()

        if batch not in job.batches:
            job.batches.append(batch)


# ==================== NEW: NOTIFICATION HELPER ====================
def send_notifications_for_job(job):
    """Send push notifications to all eligible batch subscribers"""
    try:
        from app.routes.notifications import notify_batch

        total_sent = 0
        for batch in job.batches:
            count = notify_batch(batch.name, job)
            total_sent += count

        if total_sent > 0:
            current_app.logger.info(f"Sent {total_sent} notifications for job {job.id}")
            return total_sent
        return 0
    except Exception as e:
        current_app.logger.error(f"Error sending notifications: {str(e)}")
        return 0


# ==================== ROUTES ====================

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated and isinstance(current_user, Admin):
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Username and password are required.', 'danger')
            return render_template('admin/login.html')

        admin = Admin.query.filter_by(username=username).first()

        if admin and admin.check_password(password):
            login_user(admin)
            flash("Login successful!", "success")
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('admin/login.html')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "success")
    return redirect(url_for('main.index'))


@bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if not isinstance(current_user, Admin):
        flash("Unauthorized access.", "danger")
        return redirect(url_for('main.index'))

    jobs = Job.query.order_by(Job.created_at.desc()).all()
    batches = Batch.query.order_by(Batch.name.desc()).all()

    return render_template('admin/dashboard.html', jobs=jobs, batches=batches)


@bp.route('/add', methods=['POST'])
@login_required
def add_job():
    if not isinstance(current_user, Admin):
        flash("Unauthorized access.", "danger")
        return redirect(url_for('main.index'))

    opportunity_type = request.form.get('opportunity_type', 'full_time')

    company_name = sanitize_input(request.form.get('company_name', ''), 200)
    role = sanitize_input(request.form.get('role', ''), 200)
    apply_link = request.form.get('apply_link', '').strip()
    description = sanitize_input(request.form.get('description', ''), 5000)
    location = sanitize_input(request.form.get('location', ''), 200)
    batch_input = request.form.get('batch_names', '')

    if not company_name or not role or not apply_link:
        flash("Company/Event name, Role/Title, and Link are required.", "danger")
        return redirect(url_for('admin.dashboard'))

    if not validate_url(apply_link):
        flash("Invalid URL format. Please use a valid http:// or https:// URL.", "danger")
        return redirect(url_for('admin.dashboard'))

    job = Job(
        company_name=company_name,
        role=role,
        apply_link=apply_link,
        description=description,
        location=location,
        is_internship=(opportunity_type == 'internship'),
        is_hackathon=(opportunity_type == 'hackathon')
    )

    if opportunity_type == 'full_time':
        salary = validate_number(request.form.get('salary'), 'Salary', 0, 1000)
        job.salary = salary

    elif opportunity_type == 'internship':
        stipend = validate_number(request.form.get('stipend'), 'Stipend', 0, 1000000)
        job.stipend = stipend

    elif opportunity_type == 'hackathon':
        prize_money = validate_number(request.form.get('prize_money'), 'Prize Money', 0, 100000000)
        job.prize_money = prize_money

        deadline_str = request.form.get('deadline', '').strip()
        if deadline_str:
            try:
                job.deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
            except ValueError:
                flash("Invalid deadline format.", "warning")

    process_batches(batch_input, job)

    db.session.add(job)
    db.session.commit()

    # ==================== NEW: SEND PUSH NOTIFICATIONS ====================
    notifications_sent = send_notifications_for_job(job)

    if notifications_sent > 0:
        flash(f"New {job.job_type} added successfully! {notifications_sent} notifications sent.", "success")
    else:
        flash(f"New {job.job_type} added successfully!", "success")

    return redirect(url_for('admin.dashboard'))


@bp.route('/edit/<int:job_id>', methods=['GET', 'POST'])
@login_required
def edit_job(job_id):
    if not isinstance(current_user, Admin):
        flash("Unauthorized access.", "danger")
        return redirect(url_for('main.index'))

    job = Job.query.get_or_404(job_id)
    batches = Batch.query.order_by(Batch.name.desc()).all()

    if request.method == 'POST':
        opportunity_type = request.form.get('opportunity_type', 'full_time')

        company_name = sanitize_input(request.form.get('company_name', ''), 200)
        role = sanitize_input(request.form.get('role', ''), 200)
        apply_link = request.form.get('apply_link', '').strip()
        description = sanitize_input(request.form.get('description', ''), 5000)
        location = sanitize_input(request.form.get('location', ''), 200)
        batch_input = request.form.get('batch_names', '')

        if not company_name or not role or not apply_link:
            flash("Company/Event name, Role/Title, and Link are required.", "danger")
            return redirect(url_for('admin.edit_job', job_id=job_id))

        if not validate_url(apply_link):
            flash("Invalid URL format.", "danger")
            return redirect(url_for('admin.edit_job', job_id=job_id))

        job.company_name = company_name
        job.role = role
        job.apply_link = apply_link
        job.description = description
        job.location = location

        job.is_internship = (opportunity_type == 'internship')
        job.is_hackathon = (opportunity_type == 'hackathon')

        job.salary = None
        job.stipend = None
        job.prize_money = None
        job.deadline = None

        if opportunity_type == 'full_time':
            salary = validate_number(request.form.get('salary'), 'Salary', 0, 1000)
            job.salary = salary

        elif opportunity_type == 'internship':
            stipend = validate_number(request.form.get('stipend'), 'Stipend', 0, 1000000)
            job.stipend = stipend

        elif opportunity_type == 'hackathon':
            prize_money = validate_number(request.form.get('prize_money'), 'Prize Money', 0, 100000000)
            job.prize_money = prize_money

            deadline_str = request.form.get('deadline', '').strip()
            if deadline_str:
                try:
                    job.deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
                except ValueError:
                    flash("Invalid deadline format.", "warning")

        job.batches.clear()
        process_batches(batch_input, job)

        db.session.commit()
        flash(f"{job.job_type} updated successfully!", "success")
        return redirect(url_for('admin.dashboard'))

    return render_template('admin/edit_job.html', job=job, batches=batches)


@bp.route('/delete/<int:job_id>', methods=['POST'])
@login_required
def delete_job(job_id):
    if not isinstance(current_user, Admin):
        flash("Unauthorized access.", "danger")
        return redirect(url_for('main.index'))

    job = Job.query.get_or_404(job_id)
    job_type = job.job_type
    db.session.delete(job)
    db.session.commit()
    flash(f"{job_type} deleted successfully!", "success")
    return redirect(url_for('admin.dashboard'))