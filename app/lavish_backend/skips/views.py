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
from .helpers import json_response, error_response
from .customer_api import (
    cancel_subscription, pause_subscription, resume_subscription, 
    change_subscription_frequency, subscription_management_options
)

logger = logging.getLogger(__name__)


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
def subscription_renewal_info(request, subscription_id):
    """
    Get detailed renewal information for a subscription
    
    GET /api/skips/subscriptions/{subscription_id}/renewal-info/
    """
    try:
        subscription = get_object_or_404(
            CustomerSubscription,
            shopify_id=subscription_id
        )
        
        # Calculate renewal urgency
        now = timezone.now()
        next_billing = subscription.next_billing_date
        
        if not next_billing:
            return error_response('No next billing date found', status=404)
        
        days_until_renewal = (next_billing.date() - now.date()).days
        
        # Calculate cycle progress
        last_billing = subscription.last_billing_date or now - timedelta(days=30)
        cycle_length = (next_billing.date() - last_billing.date()).days
        days_in_cycle = (now.date() - last_billing.date()).days
        cycle_progress = min(100, max(0, (days_in_cycle / cycle_length) * 100))
        
        # Determine urgency level
        if days_until_renewal <= 3:
            urgency_level = 'high'
            urgency_text = f'{days_until_renewal} days'
            urgency_message = 'Renewal imminent - Action required'
        elif days_until_renewal <= 7:
            urgency_level = 'medium'
            urgency_text = f'{days_until_renewal} days'
            urgency_message = 'Renewal approaching - Be prepared'
        else:
            urgency_level = 'low'
            urgency_text = f'{days_until_renewal} days'
            urgency_message = 'Renewal scheduled - No action needed'
        
        # Calculate cutoff date
        cutoff_date = next_billing.date() - timedelta(days=14)
        days_until_cutoff = (cutoff_date - now.date()).days
        
        renewal_info = {
            'subscription_id': subscription.shopify_id,
            'next_billing_date': next_billing.isoformat(),
            'last_billing_date': last_billing.isoformat(),
            'days_until_renewal': days_until_renewal,
            'urgency_level': urgency_level,
            'urgency_text': urgency_text,
            'urgency_message': urgency_message,
            'cycle_progress': {
                'percentage': round(cycle_progress, 1),
                'days_in_cycle': days_in_cycle,
                'cycle_length': cycle_length,
                'days_remaining': max(0, cycle_length - days_in_cycle)
            },
            'cutoff_date': cutoff_date.isoformat(),
            'days_until_cutoff': days_until_cutoff,
            'billing_amount': str(subscription.price or '0.00'),
            'billing_frequency': f"{subscription.billing_policy_interval_count} {subscription.billing_policy_interval.lower()}ly"
        }
        
        return json_response({
            'success': True,
            'renewal_info': renewal_info
        })
        
    except Exception as e:
        logger.error(f'Error getting renewal info: {str(e)}', exc_info=True)
        return error_response('An error occurred while fetching renewal information', status=500)


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
        
        # Calculate cutoff date information
        from datetime import date
        cutoff_date = subscription.get_cutoff_date()
        days_until_cutoff = None
        cutoff_urgency = 'normal'
        
        if cutoff_date:
            today = date.today()
            days_until_cutoff = (cutoff_date - today).days
            if days_until_cutoff <= 3:
                cutoff_urgency = 'urgent'
            elif days_until_cutoff <= 7:
                cutoff_urgency = 'warning'
        
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
                'cutoff_info': {
                    'cutoff_date': cutoff_date.isoformat() if cutoff_date else None,
                    'days_until_cutoff': days_until_cutoff,
                    'urgency': cutoff_urgency,
                    'message': f'Order cutoff in {days_until_cutoff} days' if days_until_cutoff and days_until_cutoff > 0 else 'Cutoff passed' if days_until_cutoff and days_until_cutoff <= 0 else 'No cutoff set'
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
        
        # Calculate cutoff date information
        from datetime import date
        cutoff_date = subscription.get_cutoff_date()
        days_until_cutoff = None
        cutoff_urgency = 'normal'
        
        if cutoff_date:
            today = date.today()
            days_until_cutoff = (cutoff_date - today).days
            if days_until_cutoff <= 3:
                cutoff_urgency = 'urgent'
            elif days_until_cutoff <= 7:
                cutoff_urgency = 'warning'
        
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
            },
            'cutoff_info': {
                'cutoff_date': cutoff_date.isoformat() if cutoff_date else None,
                'days_until_cutoff': days_until_cutoff,
                'urgency': cutoff_urgency,
                'message': f'Order cutoff in {days_until_cutoff} days' if days_until_cutoff and days_until_cutoff > 0 else 'Cutoff passed' if days_until_cutoff and days_until_cutoff <= 0 else 'No cutoff set'
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
