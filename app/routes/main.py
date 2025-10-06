from flask import Blueprint, render_template, request
from app.models import Job

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    # Get filter parameters
    batch = request.args.get('batch', '')
    experience = request.args.get('experience', '')
    sort = request.args.get('sort', 'latest')

    # Query jobs
    query = Job.query.filter_by(is_active=True)

    if batch:
        query = query.filter_by(batch=batch)
    if experience:
        query = query.filter_by(experience_level=experience)

    # Sort
    if sort == 'package_high':
        query = query.order_by(Job.package_max.desc())
    elif sort == 'package_low':
        query = query.order_by(Job.package_min.asc())
    else:
        query = query.order_by(Job.posted_date.desc())

    jobs = query.all()

    # Get unique batches and experience levels for filters
    batches = ['2024', '2025', '2026']
    experiences = ['Fresher', 'SDE-1', 'SDE-2']

    return render_template('index.html',
                         jobs=jobs,
                         batches=batches,
                         experiences=experiences,
                         current_batch=batch,
                         current_experience=experience,
                         current_sort=sort)
@bp.route('/debug')
def debug():
    from flask import current_app
    import os
    template_path = current_app.template_folder
    abs_path = os.path.abspath(template_path)
    return f"Relative: {template_path}<br>Absolute: {abs_path}"