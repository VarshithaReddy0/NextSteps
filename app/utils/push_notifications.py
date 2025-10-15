"""Utility functions for push notifications"""
from pywebpush import webpush, WebPushException
import json
import logging
from app import db
from app.models import PushSubscription

logger = logging.getLogger(__name__)


def send_push_notification(subscription_info, message_data, vapid_private_key, vapid_claims):
    """Send a push notification to a single subscriber"""
    try:
        if isinstance(subscription_info, str):
            subscription_info = json.loads(subscription_info)

        webpush(
            subscription_info=subscription_info,
            data=json.dumps(message_data),
            vapid_private_key=vapid_private_key,
            vapid_claims=vapid_claims
        )
        return True

    except WebPushException as e:
        logger.error(f"WebPush error: {e}")
        if e.response and e.response.status_code in [404, 410]:
            endpoint = subscription_info.get('endpoint')
            if endpoint:
                expired = PushSubscription.query.filter_by(endpoint=endpoint).first()
                if expired:
                    db.session.delete(expired)
                    db.session.commit()
        return False

    except Exception as e:
        logger.error(f"Push error: {e}")
        return False


def notify_batch(job, app_context):
    """Send notifications for new job"""
    with app_context:
        try:
            from flask import current_app

            vapid_private_key = current_app.config.get('VAPID_PRIVATE_KEY')
            vapid_claims = current_app.config.get('VAPID_CLAIMS')

            if not vapid_private_key:
                logger.error("VAPID keys not configured")
                return

            target_batches = [b.name for b in job.batches] if job.batches else []

            if target_batches:
                subscriptions = PushSubscription.query.filter(
                    PushSubscription.batch.in_(target_batches),
                    PushSubscription.is_active == True
                ).all()
            else:
                subscriptions = PushSubscription.query.filter_by(is_active=True).all()

            if not subscriptions:
                logger.info("No subscribers")
                return

            job_type = "Hackathon" if job.is_hackathon else ("Internship" if job.is_internship else "Job")

            notification_data = {
                "title": f"🎉 New {job_type}: {job.company_name}",
                "body": f"{job.role} - {job.location}",
                "icon": "/static/images/logo.png",
                "url": f"/?job_id={job.id}"
            }

            success = 0
            fail = 0

            for sub in subscriptions:
                try:
                    subscription_info = json.loads(sub.subscription_json)
                    if send_push_notification(subscription_info, notification_data, vapid_private_key, vapid_claims):
                        success += 1
                    else:
                        fail += 1
                except Exception as e:
                    logger.error(f"Error: {e}")
                    fail += 1

            logger.info(f"Sent: {success}, Failed: {fail}")

        except Exception as e:
            logger.error(f"Notify error: {e}")


def notify_batch_async(job):
    """Async wrapper"""
    from flask import current_app
    from threading import Thread

    app_context = current_app._get_current_object().app_context()
    thread = Thread(target=notify_batch, args=(job, app_context))
    thread.daemon = True
    thread.start()


def send_custom_notification(title, message, target_batches, notification_type, url, app_context):
    """Send custom notification"""
    with app_context:
        try:
            from flask import current_app

            vapid_private_key = current_app.config.get('VAPID_PRIVATE_KEY')
            vapid_claims = current_app.config.get('VAPID_CLAIMS')

            if target_batches:
                subscriptions = PushSubscription.query.filter(
                    PushSubscription.batch.in_(target_batches),
                    PushSubscription.is_active == True
                ).all()
            else:
                subscriptions = PushSubscription.query.filter_by(is_active=True).all()

            emoji_map = {'info': '📢', 'success': '✅', 'warning': '⚠️', 'alert': '🚨'}
            icon = emoji_map.get(notification_type, '📢')

            notification_data = {
                "title": f"{icon} {title}",
                "body": message,
                "icon": "/static/images/logo.png",
                "url": url
            }

            success = 0
            for sub in subscriptions:
                try:
                    subscription_info = json.loads(sub.subscription_json)
                    if send_push_notification(subscription_info, notification_data, vapid_private_key, vapid_claims):
                        success += 1
                except:
                    pass

            logger.info(f"Custom notification sent to {success} users")
            return {'success': True, 'sent': success}

        except Exception as e:
            logger.error(f"Custom notification error: {e}")
            return {'success': False, 'error': str(e)}


def send_custom_notification_async(title, message, target_batches, notification_type, url):
    """Async wrapper for custom notifications"""
    from flask import current_app
    from threading import Thread

    app_context = current_app._get_current_object().app_context()
    thread = Thread(target=send_custom_notification, args=(title, message, target_batches, notification_type, url, app_context))
    thread.daemon = True
    thread.start()