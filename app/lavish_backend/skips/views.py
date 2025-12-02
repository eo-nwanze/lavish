"""
API Views for Subscription Skip Management

Provides REST endpoints for frontend skip functionality
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
from .models import (
    SubscriptionSkip,
    SubscriptionSkipPolicy,
    SkipNotification
)

logger = logging.getLogger(__name__)


def json_response(data, status=200):
    """Helper to return consistent JSON responses"""
    return JsonResponse(data, status=status)


def error_response(message, status=400, errors=None):
    """Helper to return error responses"""
    response = {'success': False, 'error': message}
    if errors:
        response['errors'] = errors
    return JsonResponse(response, status=status)


@csrf_exempt
@require_http_methods(["POST"])
def skip_next_payment(request):
    """
    Skip the next payment for a subscription
    
    POST /customers/subscriptions/skip/
    Body: {
        "subscription_id": "gid://shopify/SubscriptionContract/123",
        "reason": "Going on vacation" (optional),
        "reason_details": "Will be away for 2 weeks" (optional)
    }
    """
    try:
        data = json.loads(request.body)
        subscription_id = data.get('subscription_id')
        reason = data.get('reason', '')
        reason_details = data.get('reason_details', '')
        
        if not subscription_id:
            return error_response('subscription_id is required')
        
        # Get subscription
        subscription = get_object_or_404(
            CustomerSubscription,
            shopify_subscription_contract_id=subscription_id
        )
        
        # Check if skip is allowed
        can_skip, message = subscription.can_skip_next_order()
        if not can_skip:
            return error_response(message, status=403)
        
        # Calculate new dates
        new_order_date = subscription.calculate_next_order_date_after_skip()
        new_billing_date = new_order_date  # Assuming billing and order dates align
        
        # Create skip record
        with transaction.atomic():
            skip = SubscriptionSkip.objects.create(
                subscription=subscription,
                skip_type='manual',
                status='pending',
                original_order_date=subscription.next_order_date,
                original_billing_date=subscription.next_billing_date,
                new_order_date=new_order_date,
                new_billing_date=new_billing_date,
                reason=reason[:100],  # Limit to field max_length
                reason_details=reason_details,
                skip_fee_charged=subscription.skip_policy.skip_fee if subscription.skip_policy else 0.00
            )
            
            # Auto-confirm skip (can be changed to require admin approval)
            skip.confirm_skip()
            
            # Send notification via email_manager
            from .notification_service import SkipNotificationService
            SkipNotificationService.send_skip_confirmed_notification(skip, subscription)
        
        logger.info(f'Skip created for subscription {subscription_id}: {skip.pk}')
        
        return json_response({
            'success': True,
            'message': 'Your payment has been successfully skipped',
            'skip': {
                'id': skip.pk,
                'original_date': skip.original_order_date.isoformat(),
                'new_date': skip.new_order_date.isoformat(),
                'status': skip.status,
                'fee_charged': str(skip.skip_fee_charged)
            },
            'subscription': {
                'next_order_date': subscription.next_order_date.isoformat(),
                'skips_remaining': subscription.get_skips_remaining()
            }
        })
        
    except CustomerSubscription.DoesNotExist:
        return error_response('Subscription not found', status=404)
    except json.JSONDecodeError:
        return error_response('Invalid JSON in request body')
    except Exception as e:
        logger.error(f'Error creating skip: {str(e)}', exc_info=True)
        return error_response('An error occurred while processing your skip request', status=500)


@require_http_methods(["GET"])
def subscription_details(request, subscription_id):
    """
    Get subscription details including skip information
    
    GET /customers/subscriptions/<subscription_id>/
    """
    try:
        subscription = get_object_or_404(
            CustomerSubscription,
            shopify_subscription_contract_id=subscription_id
        )
        
        # Get recent skips
        recent_skips = subscription.skips.filter(
            status='confirmed'
        ).order_by('-created_at')[:5]
        
        # Check skip eligibility
        can_skip, skip_message = subscription.can_skip_next_order()
        
        return json_response({
            'success': True,
            'subscription': {
                'id': subscription.shopify_subscription_contract_id,
                'name': subscription.subscription_name,
                'status': subscription.status,
                'billing_cycle': subscription.billing_cycle,
                'next_order_date': subscription.next_order_date.isoformat(),
                'next_billing_date': subscription.next_billing_date.isoformat(),
                'customer': {
                    'email': subscription.customer_email,
                    'name': subscription.customer_name
                },
                'pricing': {
                    'product_price': str(subscription.product_price),
                    'shipping_price': str(subscription.shipping_price),
                    'total_price': str(subscription.total_price),
                    'currency': subscription.currency_code
                },
                'skip_info': {
                    'can_skip': can_skip,
                    'skip_message': skip_message,
                    'skips_remaining': subscription.get_skips_remaining(),
                    'skips_used_this_year': subscription.skips_used_this_year,
                    'consecutive_skips': subscription.consecutive_skips,
                    'max_skips_per_year': subscription.skip_policy.max_skips_per_year if subscription.skip_policy else 0,
                    'advance_notice_days': subscription.skip_policy.advance_notice_days if subscription.skip_policy else 0,
                    'skip_fee': str(subscription.skip_policy.skip_fee) if subscription.skip_policy else '0.00'
                },
                'recent_skips': [
                    {
                        'id': skip.pk,
                        'original_date': skip.original_order_date.isoformat(),
                        'new_date': skip.new_order_date.isoformat(),
                        'status': skip.status,
                        'created_at': skip.created_at.isoformat()
                    }
                    for skip in recent_skips
                ]
            }
        })
        
    except CustomerSubscription.DoesNotExist:
        return error_response('Subscription not found', status=404)
    except Exception as e:
        logger.error(f'Error fetching subscription details: {str(e)}', exc_info=True)
        return error_response('An error occurred', status=500)


@require_http_methods(["GET"])
def subscription_skips_list(request, subscription_id):
    """
    List all skips for a subscription
    
    GET /customers/subscriptions/<subscription_id>/skips/
    """
    try:
        subscription = get_object_or_404(
            CustomerSubscription,
            shopify_subscription_contract_id=subscription_id
        )
        
        skips = subscription.skips.all().order_by('-created_at')
        
        return json_response({
            'success': True,
            'subscription_id': subscription_id,
            'total_skips': skips.count(),
            'skips': [
                {
                    'id': skip.pk,
                    'skip_type': skip.skip_type,
                    'status': skip.status,
                    'original_order_date': skip.original_order_date.isoformat(),
                    'new_order_date': skip.new_order_date.isoformat(),
                    'reason': skip.reason,
                    'skip_fee': str(skip.skip_fee_charged),
                    'created_at': skip.created_at.isoformat(),
                    'confirmed_at': skip.confirmed_at.isoformat() if skip.confirmed_at else None
                }
                for skip in skips
            ]
        })
        
    except CustomerSubscription.DoesNotExist:
        return error_response('Subscription not found', status=404)
    except Exception as e:
        logger.error(f'Error listing skips: {str(e)}', exc_info=True)
        return error_response('An error occurred', status=500)


@require_http_methods(["GET"])
def skip_quota(request, subscription_id):
    """
    Get skip quota information for a subscription
    
    GET /customers/subscriptions/<subscription_id>/skip-quota/
    """
    try:
        subscription = get_object_or_404(
            CustomerSubscription,
            shopify_subscription_contract_id=subscription_id
        )
        
        if not subscription.skip_policy:
            return json_response({
                'success': True,
                'has_skip_policy': False,
                'message': 'No skip policy configured for this subscription'
            })
        
        can_skip, message = subscription.can_skip_next_order()
        
        return json_response({
            'success': True,
            'has_skip_policy': True,
            'can_skip_next_order': can_skip,
            'skip_message': message,
            'quota': {
                'max_skips_per_year': subscription.skip_policy.max_skips_per_year,
                'skips_used_this_year': subscription.skips_used_this_year,
                'skips_remaining': subscription.get_skips_remaining(),
                'max_consecutive_skips': subscription.skip_policy.max_consecutive_skips,
                'current_consecutive_skips': subscription.consecutive_skips,
                'advance_notice_days': subscription.skip_policy.advance_notice_days,
                'skip_fee': str(subscription.skip_policy.skip_fee)
            }
        })
        
    except CustomerSubscription.DoesNotExist:
        return error_response('Subscription not found', status=404)
    except Exception as e:
        logger.error(f'Error fetching skip quota: {str(e)}', exc_info=True)
        return error_response('An error occurred', status=500)


@csrf_exempt
@require_http_methods(["DELETE", "POST"])
def cancel_skip(request, skip_id):
    """
    Cancel a pending skip
    
    DELETE /customers/subscriptions/skip/<skip_id>/cancel/
    POST /customers/subscriptions/skip/<skip_id>/cancel/
    """
    try:
        skip = get_object_or_404(SubscriptionSkip, pk=skip_id)
        
        # Only allow cancelling pending skips
        if skip.status != 'pending':
            return error_response(
                f'Cannot cancel skip with status: {skip.status}',
                status=400
            )
        
        # Parse reason if provided
        reason = ''
        if request.method == 'POST' and request.body:
            try:
                data = json.loads(request.body)
                reason = data.get('reason', '')
            except json.JSONDecodeError:
                pass
        
        skip.cancel_skip(reason=reason)
        
        logger.info(f'Skip {skip_id} cancelled')
        
        return json_response({
            'success': True,
            'message': 'Skip successfully cancelled',
            'skip': {
                'id': skip.pk,
                'status': skip.status,
                'cancelled_at': skip.cancelled_at.isoformat()
            }
        })
        
    except SubscriptionSkip.DoesNotExist:
        return error_response('Skip not found', status=404)
    except ValidationError as e:
        return error_response(str(e))
    except Exception as e:
        logger.error(f'Error cancelling skip: {str(e)}', exc_info=True)
        return error_response('An error occurred', status=500)


@require_http_methods(["GET"])
def customer_subscriptions(request):
    """
    List all subscriptions for a customer
    
    GET /customers/subscriptions/?email=customer@example.com
    GET /customers/subscriptions/?shopify_customer_id=123
    """
    try:
        email = request.GET.get('email')
        shopify_customer_id = request.GET.get('shopify_customer_id')
        
        if not email and not shopify_customer_id:
            return error_response('email or shopify_customer_id parameter required')
        
        # Build query
        if email:
            subscriptions = CustomerSubscription.objects.filter(customer_email=email)
        else:
            subscriptions = CustomerSubscription.objects.filter(
                shopify_customer_id=shopify_customer_id
            )
        
        subscriptions = subscriptions.order_by('-next_order_date')
        
        return json_response({
            'success': True,
            'count': subscriptions.count(),
            'subscriptions': [
                {
                    'id': sub.shopify_subscription_contract_id,
                    'name': sub.subscription_name,
                    'status': sub.status,
                    'billing_cycle': sub.billing_cycle,
                    'next_order_date': sub.next_order_date.isoformat(),
                    'total_price': str(sub.total_price),
                    'currency': sub.currency_code,
                    'skips_remaining': sub.get_skips_remaining()
                }
                for sub in subscriptions
            ]
        })
        
    except Exception as e:
        logger.error(f'Error listing customer subscriptions: {str(e)}', exc_info=True)
        return error_response('An error occurred', status=500)


# Health check endpoint
@require_http_methods(["GET"])
def health_check(request):
    """Simple health check endpoint"""
    return json_response({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'service': 'subscription-skips-api'
    })
