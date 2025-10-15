from pywebpush import webpush, WebPushException
from app.models import PushSubscription
from app import db
from datetime import datetime
from flask import current_app
import json
import logging

logger = logging.getLogger(__name__)


def send_job_notification(job):
    """
    Send push notification when a new job is posted
    Sends to all batches associated with the job
    """
    if not job.batches:
        logger.warning(f'Job {job.id} has no batches assigned')
        return 0, 0

    total_success = 0
    total_failed = 0

    for batch in job.batches:
        success, failed = send_notification_to_batch(
            batch_name=batch.name,
            title=f'New {job.job_type}: {job.role}',
            body=f'{job.company_name} • {job.location}',
            url=f'/?job={job.id}',  # You can create a detail page later
            tag=f'job-{job.id}'
        )
        total_success += success
        total_failed += failed

    logger.info(f'Job notification sent: {total_success} success, {total_failed} failed')
    return total_success, total_failed


def send_manual_notification(batch_name, title, message, url='/'):
    """
    Send manual notification from admin panel
    """
    return send_notification_to_batch(
        batch_name=batch_name,
        title=title,
        body=message,
        url=url,
        tag=f'admin-{datetime.utcnow().timestamp()}'
    )


def send_notification_to_batch(batch_name, title, body, url='/', tag='notification'):
    """
    Core function to send push notifications to a specific batch
    """
    subscriptions = PushSubscription.query.filter_by(
        batch=batch_name,
        is_active=True
    ).all()

    if not subscriptions:
        logger.info(f'No active subscriptions for batch {batch_name}')
        return 0, 0

    payload = {
        'title': title,
        'body': body,
        'icon': '/static/icon-192x192.png',  # Make sure this exists
        'badge': '/static/badge-72x72.png',  # Make sure this exists
        'url': url,
        'tag': tag,
        'requireInteraction': False,
        'timestamp': int(datetime.utcnow().timestamp() * 1000)
    }

    vapid_private = current_app.config.get('VAPID_PRIVATE_KEY')
    vapid_email = current_app.config.get('VAPID_CLAIM_EMAIL')

    if not vapid_private or not vapid_email:
        logger.error('VAPID keys not configured!')
        return 0, len(subscriptions)

    vapid_claims = {'sub': vapid_email}

    success_count = 0
    failed_count = 0

    for sub in subscriptions:
        try:
            response = webpush(
                subscription_info=sub.to_dict(),
                data=json.dumps(payload),
                vapid_private_key=vapid_private,
                vapid_claims=vapid_claims,
                timeout=10
            )

            if response.status_code in [200, 201]:
                sub.last_notified = datetime.utcnow()
                success_count += 1
                logger.debug(f'Push sent successfully to {sub.endpoint[:50]}')
            else:
                logger.warning(f'Push returned {response.status_code} for {sub.endpoint[:50]}')
                failed_count += 1

        except WebPushException as e:
            logger.error(f'WebPush failed: {str(e)}')

            # Handle expired/invalid subscriptions
            if e.response and e.response.status_code in [404, 410]:
                sub.is_active = False
                logger.info(f'Marked subscription as inactive: {sub.endpoint[:50]}')

            failed_count += 1

        except Exception as e:
            logger.error(f'Unexpected error sending push: {str(e)}')
            failed_count += 1

    db.session.commit()
    logger.info(f'Batch {batch_name}: {success_count} sent, {failed_count} failed')

    return success_count, failed_count