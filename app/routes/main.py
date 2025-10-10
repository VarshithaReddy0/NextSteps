from flask import Blueprint, render_template, request

from app import db
from app.models import Job, Batch

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    batch_filter = request.args.get('batch', None)
    experience = request.args.get('experience', None)
    sort = request.args.get('sort', 'latest')

    query = Job.query.filter_by(is_active=True)

    if batch_filter:
        query = query.join(Job.batches).filter(Batch.name == batch_filter)

    if experience and experience.isdigit():
        exp_value = int(experience)
        query = query.filter(
            (Job.min_experience <= exp_value) &
            ((Job.max_experience >= exp_value) | (Job.max_experience == None))
        )

    if sort == 'package_high':
        query = query.order_by(Job.package_max.desc(), Job.package_min.desc())
    elif sort == 'package_low':
        query = query.order_by(Job.package_min.asc(), Job.package_max.asc())
    else:
        query = query.order_by(Job.posted_date.desc())

    jobs = query.paginate(page=page, per_page=8)

    # Get unique batches, exclude any with commas, sort descending
    all_batches = Batch.query.all()
    batches = sorted(
        list(set([b.name for b in all_batches if ',' not in b.name])),
        reverse=True
    )

    experiences = ['0', '1', '2', '3', '4', '5']

    return render_template(
        'index.html',
        jobs=jobs,
        batches=batches,
        experiences=experiences,
        current_batch=batch_filter,
        current_experience=experience,
        current_sort=sort
    )