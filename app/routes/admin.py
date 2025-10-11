from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import Admin, Job, Batch
import re

bp = Blueprint('admin', __name__, url_prefix='/admin')


# ==================== HELPER FUNCTIONS ====================

def validate_url(url):
    """Validate URL format"""
    if not url:
        return False
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None


def sanitize_input(text, max_length=500):
    """Basic input sanitization"""
    if not text:
        return text
    # Remove any potential script tags
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    # Remove any potential HTML tags for safety
    text = re.sub(r'<[^>]+>', '', text)
    # Trim to max length
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
    Always splits comma-separated values and creates individual batch records.
    """
    if not batch_input:
        return

    # Split by comma and clean up
    batch_names = [name.strip() for name in batch_input.split(',') if name.strip()]

    for name in batch_names:
        # Sanitize batch name
        name = sanitize_input(name, 10)

        # Validate: batch name should be a simple value (no commas)
        if ',' in name:
            flash(f"Invalid batch name: {name}. Please enter single years only.", "warning")
            continue

        # Find or create batch
        batch = Batch.query.filter_by(name=name).first()
        if not batch:
            batch = Batch(name=name)
            db.session.add(batch)
            db.session.flush()  # Get the batch ID before linking

        # Link to job if not already linked
        if batch not in job.batches:
            job.batches.append(batch)


# ==================== ROUTES ====================

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated and isinstance(current_user, Admin):
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        # Basic input validation
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

    jobs = Job.query.order_by(Job.posted_date.desc()).all()

    if request.method == 'POST':
        # Get and sanitize form data
        title = sanitize_input(request.form.get('title', ''), 200)
        company = sanitize_input(request.form.get('company', ''), 200)
        apply_link = request.form.get('apply_link', '').strip()
        description = sanitize_input(request.form.get('description', ''), 5000)
        location = sanitize_input(request.form.get('location', ''), 200)
        batch_input = request.form.get('batch_names', '')

        # Validate required fields
        if not title or not company or not apply_link:
            flash("Title, company, and apply link are required fields.", "danger")
            return redirect(url_for('admin.dashboard'))

        # Validate URL
        if not validate_url(apply_link):
            flash("Invalid URL format. Please use a valid http:// or https:// URL.", "danger")
            return redirect(url_for('admin.dashboard'))

        # Validate and process numeric fields
        min_experience = validate_number(request.form.get('min_experience'), 'Minimum Experience', 0, 50)
        max_experience = validate_number(request.form.get('max_experience'), 'Maximum Experience', 0, 50)
        package_min = validate_number(request.form.get('package_min'), 'Minimum Package', 0, 1000)
        package_max = validate_number(request.form.get('package_max'), 'Maximum Package', 0, 1000)

        # Validate experience range
        if min_experience is not None and max_experience is not None:
            if min_experience > max_experience:
                flash("Minimum experience cannot be greater than maximum experience.", "danger")
                return redirect(url_for('admin.dashboard'))

        # Validate package range
        if package_min is not None and package_max is not None:
            if package_min > package_max:
                flash("Minimum package cannot be greater than maximum package.", "danger")
                return redirect(url_for('admin.dashboard'))

        # Create job
        job = Job(
            title=title,
            company=company,
            apply_link=apply_link,
            description=description,
            location=location,
            min_experience=min_experience,
            max_experience=max_experience,
            package_min=package_min,
            package_max=package_max,
        )

        # Process batches
        process_batches(batch_input, job)

        db.session.add(job)
        db.session.commit()
        flash("New job added successfully!", "success")
        return redirect(url_for('admin.dashboard'))

    batches = Batch.query.all()
    return render_template('admin/dashboard.html', jobs=jobs, batches=batches)


@bp.route('/edit/<int:job_id>', methods=['GET', 'POST'])
@login_required
def edit_job(job_id):
    job = Job.query.get_or_404(job_id)

    if request.method == 'POST':
        # Get and sanitize form data
        title = sanitize_input(request.form.get('title', ''), 200)
        company = sanitize_input(request.form.get('company', ''), 200)
        apply_link = request.form.get('apply_link', '').strip()
        description = sanitize_input(request.form.get('description', ''), 5000)
        location = sanitize_input(request.form.get('location', ''), 200)
        batch_input = request.form.get('batch_names', '')

        # Validate required fields
        if not title or not company or not apply_link:
            flash("Title, company, and apply link are required fields.", "danger")
            return redirect(url_for('admin.edit_job', job_id=job_id))

        # Validate URL
        if not validate_url(apply_link):
            flash("Invalid URL format. Please use a valid http:// or https:// URL.", "danger")
            return redirect(url_for('admin.edit_job', job_id=job_id))

        # Validate and process numeric fields
        min_experience = validate_number(request.form.get('min_experience'), 'Minimum Experience', 0, 50)
        max_experience = validate_number(request.form.get('max_experience'), 'Maximum Experience', 0, 50)
        package_min = validate_number(request.form.get('package_min'), 'Minimum Package', 0, 1000)
        package_max = validate_number(request.form.get('package_max'), 'Maximum Package', 0, 1000)

        # Validate experience range
        if min_experience is not None and max_experience is not None:
            if min_experience > max_experience:
                flash("Minimum experience cannot be greater than maximum experience.", "danger")
                return redirect(url_for('admin.edit_job', job_id=job_id))

        # Validate package range
        if package_min is not None and package_max is not None:
            if package_min > package_max:
                flash("Minimum package cannot be greater than maximum package.", "danger")
                return redirect(url_for('admin.edit_job', job_id=job_id))

        # Update job
        job.title = title
        job.company = company
        job.apply_link = apply_link
        job.description = description
        job.location = location
        job.min_experience = min_experience
        job.max_experience = max_experience
        job.package_min = package_min
        job.package_max = package_max

        # Clear and update batches
        job.batches.clear()
        process_batches(batch_input, job)

        db.session.commit()
        flash("Job updated successfully!", "success")
        return redirect(url_for('admin.dashboard'))

    batches = Batch.query.all()
    return render_template('admin/edit_job.html', job=job, batches=batches)


@bp.route('/delete/<int:job_id>', methods=['POST'])
@login_required
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    flash("Job deleted successfully!", "success")
    return redirect(url_for('admin.dashboard'))