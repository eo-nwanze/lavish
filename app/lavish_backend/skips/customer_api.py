"""
Customer-facing subscription management API endpoints
"""

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
import json
import logging

from customer_subscriptions.models import CustomerSubscription
from skips.models import SubscriptionSkip, SubscriptionSkipPolicy
from skips.helpers import json_response, error_response
from customer_subscriptions.email_service import SubscriptionEmailService
from customer_subscriptions.bidirectional_sync import SubscriptionBidirectionalSync

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def cancel_subscription(request, subscription_id):
    """
    Customer-initiated subscription cancellation
    
    POST /api/subscriptions/cancel/
    Body: {
        "subscription_id": "gid://shopify/SubscriptionContract/123",
        "reason": "too_expensive",
        "feedback": "Need to save money for holidays",
        "confirm": true
    }
    """
    try:
        data = json.loads(request.body)
        subscription_id = data.get('subscription_id')
        reason = data.get('reason', '')
        feedback = data.get('feedback', '')
        confirm = data.get('confirm', False)
        
        if not subscription_id:
            return error_response('subscription_id is required')
        
        if not confirm:
            return error_response('Please confirm cancellation by setting confirm=true', status=400)
        
        # Get subscription
        subscription = get_object_or_404(
            CustomerSubscription,
            shopify_id=subscription_id
        )
        
        # Verify subscription can be cancelled
        if subscription.status not in ['ACTIVE', 'PAUSED']:
            return error_response(f'Cannot cancel subscription with status: {subscription.status}', status=400)
        
        # Check for pending skips - PREVENT CANCELLATION IF EXISTS
        pending_skips = subscription.skips.filter(status='pending').count()
        if pending_skips > 0:
            return error_response(
                f'Cannot cancel subscription with {pending_skips} pending skip request(s). Please cancel or complete the skip(s) before cancelling.', 
                status=400
            )
        
        # Process cancellation
        with transaction.atomic():
            sync_service = SubscriptionBidirectionalSync()
            result = sync_service.cancel_subscription_in_shopify(subscription)
            
            if not result.get('success'):
                return error_response(result.get('message', 'Cancellation failed'), status=500)
            
            # Send confirmation email
            try:
                SubscriptionEmailService.send_cancellation_confirmation(
                    subscription, 
                    feedback_reason=reason,
                    recipient_email=subscription.customer.email
                )
            except Exception as e:
                logger.warning(f"Failed to send cancellation email: {e}")
            
            # Log cancellation
            from skips.models import SubscriptionSyncLog
            SubscriptionSyncLog.objects.create(
                operation_type='customer_cancellation',
                status='completed',
                subscriptions_processed=1,
                subscriptions_successful=1,
                subscriptions_failed=0,
                error_details=[{
                    'reason': reason,
                    'feedback': feedback,
                    'customer_email': subscription.customer.email
                }],
                store_domain='7fa66c-ac.myshopify.com'
            )
        
        logger.info(f'Customer cancelled subscription {subscription_id}')
        
        return json_response({
            'success': True,
            'message': 'Subscription cancelled successfully',
            'subscription': {
                'id': subscription.shopify_id,
                'status': 'CANCELLED',
                'cancelled_at': timezone.now().isoformat(),
                'final_delivery_date': subscription.next_delivery_date.isoformat() if subscription.next_delivery_date else None
            }
        })
        
    except CustomerSubscription.DoesNotExist:
        return error_response('Subscription not found', status=404)
    except json.JSONDecodeError:
        return error_response('Invalid JSON in request body')
    except Exception as e:
        logger.error(f'Error cancelling subscription: {str(e)}', exc_info=True)
        return error_response('An error occurred while processing cancellation', status=500)

@csrf_exempt
@require_http_methods(["POST"])
def pause_subscription(request, subscription_id):
    """
    Pause subscription for specified duration
    
    POST /api/subscriptions/pause/
    Body: {
        "subscription_id": "gid://shopify/SubscriptionContract/123",
        "duration_months": 2,
        "reason": "going on vacation"
    }
    """
    try:
        data = json.loads(request.body)
        subscription_id = data.get('subscription_id')
        duration_months = data.get('duration_months', 1)
        reason = data.get('reason', '')
        
        if not subscription_id:
            return error_response('subscription_id is required')
        
        if not 1 <= duration_months <= 6:
            return error_response('Duration must be between 1 and 6 months', status=400)
        
        # Get subscription
        subscription = get_object_or_404(
            CustomerSubscription,
            shopify_id=subscription_id
        )
        
        # Verify subscription can be paused
        if subscription.status != 'ACTIVE':
            return error_response(f'Cannot pause subscription with status: {subscription.status}', status=400)
        
        # Calculate pause end date
        from datetime import timedelta
        pause_end_date = timezone.now() + timedelta(days=duration_months * 30)
        
        # Update subscription status
        subscription.status = 'PAUSED'
        subscription.notes = f"Paused by customer for {duration_months} months. Reason: {reason}"
        subscription.save()
        
        # Cancel any pending skips during pause
        pending_skips = subscription.skips.filter(status='pending')
        for skip in pending_skips:
            skip.cancel_skip(reason="Subscription paused")
        
        logger.info(f'Customer paused subscription {subscription_id} for {duration_months} months')
        
        return json_response({
            'success': True,
            'message': f'Subscription paused for {duration_months} months',
            'subscription': {
                'id': subscription.shopify_id,
                'status': 'PAUSED',
                'paused_at': timezone.now().isoformat(),
                'pause_end_date': pause_end_date.isoformat(),
                'duration_months': duration_months
            }
        })
        
    except CustomerSubscription.DoesNotExist:
        return error_response('Subscription not found', status=404)
    except json.JSONDecodeError:
        return error_response('Invalid JSON in request body')
    except Exception as e:
        logger.error(f'Error pausing subscription: {str(e)}', exc_info=True)
        return error_response('An error occurred while processing pause', status=500)

@csrf_exempt
@require_http_methods(["POST"])
def resume_subscription(request, subscription_id):
    """
    Resume a paused subscription
    
    POST /api/subscriptions/resume/
    Body: {
        "subscription_id": "gid://shopify/SubscriptionContract/123"
    }
    """
    try:
        data = json.loads(request.body)
        subscription_id = data.get('subscription_id')
        
        if not subscription_id:
            return error_response('subscription_id is required')
        
        # Get subscription
        subscription = get_object_or_404(
            CustomerSubscription,
            shopify_id=subscription_id
        )
        
        # Verify subscription can be resumed
        if subscription.status != 'PAUSED':
            return error_response(f'Cannot resume subscription with status: {subscription.status}', status=400)
        
        # Update subscription status
        subscription.status = 'ACTIVE'
        subscription.notes = "Resumed by customer"
        subscription.save()
        
        logger.info(f'Customer resumed subscription {subscription_id}')
        
        return json_response({
            'success': True,
            'message': 'Subscription resumed successfully',
            'subscription': {
                'id': subscription.shopify_id,
                'status': 'ACTIVE',
                'resumed_at': timezone.now().isoformat(),
                'next_billing_date': subscription.next_billing_date.isoformat() if subscription.next_billing_date else None
            }
        })
        
    except CustomerSubscription.DoesNotExist:
        return error_response('Subscription not found', status=404)
    except json.JSONDecodeError:
        return error_response('Invalid JSON in request body')
    except Exception as e:
        logger.error(f'Error resuming subscription: {str(e)}', exc_info=True)
        return error_response('An error occurred while processing resume', status=500)

@csrf_exempt
@require_http_methods(["POST"])
def change_subscription_frequency(request, subscription_id):
    """
    Change subscription billing frequency
    
    POST /api/subscriptions/change-frequency/
    Body: {
        "subscription_id": "gid://shopify/SubscriptionContract/123",
        "new_interval": "MONTH",
        "new_interval_count": 2
    }
    """
    try:
        data = json.loads(request.body)
        subscription_id = data.get('subscription_id')
        new_interval = data.get('new_interval', 'MONTH')
        new_interval_count = data.get('new_interval_count', 1)
        
        if not subscription_id:
            return error_response('subscription_id is required')
        
        # Validate interval
        valid_intervals = ['WEEK', 'MONTH', 'YEAR']
        if new_interval not in valid_intervals:
            return error_response(f'Invalid interval. Must be one of: {valid_intervals}', status=400)
        
        if not 1 <= new_interval_count <= 12:
            return error_response('Interval count must be between 1 and 12', status=400)
        
        # Get subscription
        subscription = get_object_or_404(
            CustomerSubscription,
            shopify_id=subscription_id
        )
        
        # Store old values
        old_interval = subscription.billing_policy_interval
        old_count = subscription.billing_policy_interval_count
        
        # Update subscription
        subscription.billing_policy_interval = new_interval
        subscription.billing_policy_interval_count = new_interval_count
        subscription.notes = f"Changed from {old_interval} ({old_count}) to {new_interval} ({new_interval_count})"
        subscription.save()
        
        logger.info(f'Customer changed frequency for subscription {subscription_id} to {new_interval} ({new_interval_count})')
        
        return json_response({
            'success': True,
            'message': f'Billing frequency changed to every {new_interval_count} {new_interval.lower()}(s)',
            'subscription': {
                'id': subscription.shopify_id,
                'billing_interval': new_interval,
                'billing_interval_count': new_interval_count,
                'next_billing_date': subscription.next_billing_date.isoformat() if subscription.next_billing_date else None
            }
        })
        
    except CustomerSubscription.DoesNotExist:
        return error_response('Subscription not found', status=404)
    except json.JSONDecodeError:
        return error_response('Invalid JSON in request body')
    except Exception as e:
        logger.error(f'Error changing subscription frequency: {str(e)}', exc_info=True)
        return error_response('An error occurred while processing frequency change', status=500)

@require_http_methods(["GET"])
def subscription_management_options(request, subscription_id):
    """
    Get available management options for a subscription
    
    GET /api/subscriptions/{subscription_id}/options/
    """
    try:
        subscription = get_object_or_404(
            CustomerSubscription,
            shopify_id=subscription_id
        )
        
        # Check what options are available
        can_cancel = subscription.status in ['ACTIVE', 'PAUSED']
        can_pause = subscription.status == 'ACTIVE'
        can_resume = subscription.status == 'PAUSED'
        can_change_frequency = subscription.status in ['ACTIVE', 'PAUSED']
        
        # Check for pending skips - AFFECTS CANCELLATION AVAILABILITY
        pending_skips = subscription.skips.filter(status='pending').count()
        has_pending_skips = pending_skips > 0
        
        # If there are pending skips, cancellation is not allowed
        if has_pending_skips:
            can_cancel = False
        
        options = {
            'can_cancel': can_cancel,
            'can_pause': can_pause,
            'can_resume': can_resume,
            'can_change_frequency': can_change_frequency,
            'pending_skips': pending_skips,
            'has_pending_skips': has_pending_skips,
            'cancellation_blocked': has_pending_skips,
            'cancellation_block_reason': f'Cannot cancel subscription with {pending_skips} pending skip request(s). Please cancel or complete the skip(s) before cancelling.' if has_pending_skips else None,
            'available_frequencies': [
                {'interval': 'WEEK', 'count': 1, 'label': 'Weekly'},
                {'interval': 'WEEK', 'count': 2, 'label': 'Every 2 weeks'},
                {'interval': 'MONTH', 'count': 1, 'label': 'Monthly'},
                {'interval': 'MONTH', 'count': 2, 'label': 'Every 2 months'},
                {'interval': 'MONTH', 'count': 3, 'label': 'Every 3 months'},
                {'interval': 'YEAR', 'count': 1, 'label': 'Yearly'}
            ],
            'pause_durations': [
                {'months': 1, 'label': '1 month'},
                {'months': 2, 'label': '2 months'},
                {'months': 3, 'label': '3 months'},
                {'months': 6, 'label': '6 months'}
            ],
            'cancellation_reasons': [
                {'value': 'too_expensive', 'label': 'Too expensive'},
                {'value': 'not_enough_variety', 'label': 'Not enough variety'},
                {'value': 'books_not_my_taste', 'label': 'Books not my taste'},
                {'value': 'shipping_issues', 'label': 'Shipping issues'},
                {'value': 'temporary_pause', 'label': 'Temporary pause needed'},
                {'value': 'quality_issues', 'label': 'Quality issues'},
                {'value': 'other', 'label': 'Other'}
            ]
        }
        
        return json_response({
            'success': True,
            'subscription': {
                'id': subscription.shopify_id,
                'status': subscription.status,
                'name': subscription.selling_plan.name if subscription.selling_plan else 'Subscription'
            },
            'options': options
        })
        
    except CustomerSubscription.DoesNotExist:
        return error_response('Subscription not found', status=404)
    except Exception as e:
        logger.error(f'Error getting subscription options: {str(e)}', exc_info=True)
        return error_response('An error occurred', status=500)