from flask import Blueprint, render_template, request
from app import db
from app.models import Job, Batch
from sqlalchemy import or_

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    job_type = request.args.get('job_type', '')
    batch_filter = request.args.get('batch', '')
    search = request.args.get('search', '')

    # Base query - only active jobs
    query = Job.query.filter_by(is_active=True)

    # Filter by type
    if job_type == 'full_time':
        query = query.filter(Job.is_internship == False, Job.is_hackathon == False)
    elif job_type == 'internship':
        query = query.filter(Job.is_internship == True)
    elif job_type == 'hackathon':
        query = query.filter(Job.is_hackathon == True)

    # Filter by batch
    if batch_filter:
        query = query.join(Job.batches).filter(Batch.name == batch_filter)

    # Search in company name or role
    if search:
        search_term = f'%{search}%'
        query = query.filter(
            or_(
                Job.company_name.ilike(search_term),
                Job.role.ilike(search_term)
            )
        )

    # Order by newest first
    jobs = query.order_by(Job.created_at.desc()).paginate(
        page=page,
        per_page=10,
        error_out=False
    )

    # Get unique batches for filter (sorted descending)
    all_batches = Batch.query.order_by(Batch.name.desc()).all()
    batches = [batch.name for batch in all_batches]

    return render_template(
        'index.html',
        jobs=jobs,
        batches=batches,
        current_batch=batch_filter,
        current_job_type=job_type,
        current_search=search
    )