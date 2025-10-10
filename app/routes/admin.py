from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import Admin, Job, Batch

bp = Blueprint('admin', __name__, url_prefix='/admin')


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


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated and isinstance(current_user, Admin):
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
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
        title = request.form.get('title')
        company = request.form.get('company')
        apply_link = request.form.get('apply_link')
        description = request.form.get('description', '')
        location = request.form.get('location', '')
        min_experience = request.form.get('min_experience', None)
        max_experience = request.form.get('max_experience', None)
        package_min = request.form.get('package_min', None)
        package_max = request.form.get('package_max', None)
        batch_input = request.form.get('batch_names', '')

        if not title or not company or not apply_link:
            flash("Title, company, and apply link are required fields.", "danger")
        else:
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

            # Process batches using helper function
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
        job.title = request.form.get('title')
        job.company = request.form.get('company')
        job.apply_link = request.form.get('apply_link')
        job.description = request.form.get('description', '')
        job.location = request.form.get('location', '')
        job.min_experience = request.form.get('min_experience', None)
        job.max_experience = request.form.get('max_experience', None)
        job.package_min = request.form.get('package_min', None)
        job.package_max = request.form.get('package_max', None)
        batch_input = request.form.get('batch_names', '')

        # Clear existing batches
        job.batches.clear()

        # Process new batches using helper function
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