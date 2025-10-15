from flask import Blueprint, request, jsonify, current_app
from app.models import PushSubscription
from app import db
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

        endpoint = subscription_info['endpoint']

        # Check if subscription already exists
        existing = PushSubscription.query.filter_by(endpoint=endpoint).first()

        if existing:
            # Update existing subscription
            existing.batch = batch
            existing.subscription_json = json.dumps(subscription_info)
            existing.is_active = True
            current_app.logger.info(f"Updated existing subscription for batch {batch}")
        else:
            # Create new subscription
            subscription = PushSubscription(
                endpoint=endpoint,
                subscription_json=json.dumps(subscription_info),
                batch=batch,
                user_agent=request.headers.get('User-Agent'),
                ip_address=request.remote_addr
            )
            db.session.add(subscription)
            current_app.logger.info(f"New subscription added for batch {batch}")

        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'Subscribed to notifications for {batch}'
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Subscription error: {str(e)}")
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
            current_app.logger.info(f"Unsubscribed: {endpoint[:50]}")
            return jsonify({'success': True, 'message': 'Unsubscribed successfully'})

        return jsonify({'error': 'Subscription not found'}), 404

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unsubscribe error: {str(e)}")
        return jsonify({'error': 'Unsubscribe failed'}), 500