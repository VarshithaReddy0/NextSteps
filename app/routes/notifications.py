from flask import Blueprint, request, jsonify, current_app
from app.models import PushSubscription
from app import db
from pywebpush import webpush, WebPushException
import json

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/api/vapid-public-key', methods=['GET'])
def get_vapid_key():
    """Get VAPID public key for push notifications"""
    try:
        public_key = current_app.config.get('VAPID_PUBLIC_KEY')
        if not public_key:
            return jsonify({'error': 'VAPID public key not configured!'}), 500
        return jsonify({'publicKey': public_key})
    except Exception as e:
        current_app.logger.error(f'Error getting VAPID key: {str(e)}')
        return jsonify({'error': 'Failed to get VAPID key'}), 500


@notifications_bp.route('/api/subscribe', methods=['POST'])
def subscribe():
    """Subscribe to push notifications"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid or missing JSON payload'}), 400

        subscription_info = data.get('subscription')
        batch = data.get('batch')
        if not subscription_info or not isinstance(subscription_info, dict):
            return jsonify({'error': 'Invalid subscription object'}), 400
        if 'endpoint' not in subscription_info or 'keys' not in subscription_info:
            return jsonify({'error': 'Subscription missing required keys'}), 400
        if not batch or not isinstance(batch, str):
            return jsonify({'error': 'Batch missing or invalid'}), 400

        # Save subscription logic
        existing = PushSubscription.query.filter_by(endpoint=subscription_info['endpoint']).first()
        if existing:
            existing.batch = batch
            existing.is_active = True
        else:
            subscription = PushSubscription(
                endpoint=subscription_info['endpoint'],
                p256dh=subscription_info['keys']['p256dh'],
                auth=subscription_info['keys']['auth'],
                batch=batch,
                user_agent=request.headers.get('User-Agent'),
                ip_address=request.remote_addr
            )
            db.session.add(subscription)

        db.session.commit()
        return jsonify({'success': True, 'message': f'Subscribed to notifications for {batch}'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Subscription failed', 'details': str(e)}), 500


@notifications_bp.route('/api/unsubscribe', methods=['POST'])
def unsubscribe():
    """Unsubscribe from push notifications"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid or missing JSON payload'}), 400

        endpoint = data.get('endpoint')
        if not endpoint:
            return jsonify({'error': 'Missing endpoint'}), 400

        subscription = PushSubscription.query.filter_by(endpoint=endpoint).first()
        if subscription:
            subscription.is_active = False
            db.session.commit()
            return jsonify({'success': True, 'message': 'Unsubscribed successfully'})

        return jsonify({'error': 'Subscription not found'}), 404

    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Unsubscribe failed'}), 500