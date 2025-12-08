"""
Shopify Subscription Webhooks Handler
======================================

Handles webhooks from Shopify for subscription lifecycle events.
Based on: https://shopify.dev/docs/apps/build/purchase-options/subscriptions/model-subscriptions-solution

Required Webhooks:
- subscription_contracts/create
- subscription_contracts/update
- subscription_billing_attempts/success
- subscription_billing_attempts/failure
- customer_payment_methods/create
- customer_payment_methods/revoke
"""

import json
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db import transaction
from django.utils import timezone
from datetime import datetime, date
from .models import CustomerSubscription, SubscriptionBillingAttempt
from customers.models import ShopifyCustomer
from shopify_integration.enhanced_client import EnhancedShopifyAPIClient

logger = logging.getLogger('customer_subscriptions.webhooks')


def verify_shopify_webhook(request):
    """Verify webhook is from Shopify (implement HMAC verification)"""
    # TODO: Add HMAC verification for production
    # For now, we'll trust the request
    return True


@csrf_exempt
@require_POST
def subscription_contract_create_webhook(request):
    """
    Handle subscription_contracts/create webhook
    
    Fired when: Customer purchases a subscription product
    Action: Sync subscription contract to Django
    """
    if not verify_shopify_webhook(request):
        return HttpResponse('Unauthorized', status=401)
    
    try:
        data = json.loads(request.body)
        
        contract_id = data.get('admin_graphql_api_id')
        customer_data = data.get('customer', {})
        customer_id = customer_data.get('admin_graphql_api_id')
        
        logger.info(f"📥 Received subscription contract create: {contract_id}")
        
        # Get or create customer
        try:
            customer = ShopifyCustomer.objects.get(shopify_id=customer_id)
        except ShopifyCustomer.DoesNotExist:
            logger.warning(f"Customer {customer_id} not found, syncing from Shopify...")
            # Sync customer from Shopify
            from customers.realtime_sync import sync_single_customer
            customer = sync_single_customer(customer_id)
            if not customer:
                logger.error(f"Failed to sync customer {customer_id}")
                return JsonResponse({'status': 'error', 'message': 'Customer sync failed'}, status=400)
        
        # Parse billing and delivery policies
        billing_policy = data.get('billing_policy', {})
        delivery_policy = data.get('delivery_policy', {})
        
        # Get line items
        lines = data.get('lines', [])
        line_items = []
        for line in lines:
            line_items.append({
                'variant_id': line.get('variant_id'),
                'product_id': line.get('product_id'),
                'quantity': line.get('quantity'),
                'current_price': str(line.get('line_price', '0')),
                'title': line.get('title'),
                'variant_title': line.get('variant_title')
            })
        
        # Parse delivery address
        delivery_address = {}
        if 'delivery_method' in data and 'address' in data['delivery_method']:
            addr = data['delivery_method']['address']
            delivery_address = {
                'first_name': addr.get('first_name', ''),
                'last_name': addr.get('last_name', ''),
                'address1': addr.get('address1', ''),
                'address2': addr.get('address2', ''),
                'city': addr.get('city', ''),
                'province': addr.get('province', ''),
                'country': addr.get('country', ''),
                'zip': addr.get('zip', '')
            }
        
        # Create or update subscription in Django
        with transaction.atomic():
            subscription, created = CustomerSubscription.objects.update_or_create(
                shopify_id=contract_id,
                defaults={
                    'customer': customer,
                    'status': data.get('status', 'ACTIVE'),
                    'currency': data.get('currency_code', 'USD'),
                    'next_billing_date': datetime.fromisoformat(data['next_billing_date'].replace('Z', '+00:00')).date() if data.get('next_billing_date') else None,
                    'billing_policy_interval': billing_policy.get('interval', 'MONTH'),
                    'billing_policy_interval_count': billing_policy.get('interval_count', 1),
                    'delivery_policy_interval': delivery_policy.get('interval', 'MONTH'),
                    'delivery_policy_interval_count': delivery_policy.get('interval_count', 1),
                    'line_items': line_items,
                    'delivery_address': delivery_address,
                    'contract_created_at': timezone.now(),
                    'last_synced_from_shopify': timezone.now(),
                    'needs_shopify_push': False,
                }
            )
        
        action = "Created" if created else "Updated"
        logger.info(f"✅ {action} subscription in Django: {contract_id}")
        
        return JsonResponse({
            'status': 'success',
            'message': f'Subscription {action.lower()} in Django',
            'subscription_id': subscription.id
        })
        
    except Exception as e:
        logger.error(f"❌ Error handling subscription create webhook: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_POST
def subscription_contract_update_webhook(request):
    """
    Handle subscription_contracts/update webhook
    
    Fired when: Customer updates subscription in Shopify
    Action: Sync changes to Django
    """
    if not verify_shopify_webhook(request):
        return HttpResponse('Unauthorized', status=401)
    
    try:
        data = json.loads(request.body)
        
        contract_id = data.get('admin_graphql_api_id')
        
        logger.info(f"📥 Received subscription contract update: {contract_id}")
        
        # Update subscription in Django
        try:
            subscription = CustomerSubscription.objects.get(shopify_id=contract_id)
            
            with transaction.atomic():
                subscription.status = data.get('status', subscription.status)
                if data.get('next_billing_date'):
                    subscription.next_billing_date = datetime.fromisoformat(
                        data['next_billing_date'].replace('Z', '+00:00')
                    ).date()
                
                subscription.contract_updated_at = timezone.now()
                subscription.last_synced_from_shopify = timezone.now()
                subscription.needs_shopify_push = False
                subscription.save()
            
            logger.info(f"✅ Updated subscription in Django: {contract_id}")
            
            return JsonResponse({
                'status': 'success',
                'message': 'Subscription updated in Django'
            })
            
        except CustomerSubscription.DoesNotExist:
            logger.warning(f"Subscription {contract_id} not found in Django, creating...")
            # Fall back to create handler
            return subscription_contract_create_webhook(request)
        
    except Exception as e:
        logger.error(f"❌ Error handling subscription update webhook: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_POST
def subscription_billing_attempt_success_webhook(request):
    """
    Handle subscription_billing_attempts/success webhook
    
    Fired when: Billing attempt succeeds and order is created
    Action: Update billing attempt status, update next billing date
    """
    if not verify_shopify_webhook(request):
        return HttpResponse('Unauthorized', status=401)
    
    try:
        data = json.loads(request.body)
        
        attempt_id = data.get('admin_graphql_api_id')
        contract_id = data.get('subscription_contract_id')
        order_id = data.get('order_id')
        
        logger.info(f"📥 Billing attempt succeeded: {attempt_id}")
        
        # Update subscription
        try:
            subscription = CustomerSubscription.objects.get(shopify_id=contract_id)
            
            with transaction.atomic():
                # Update billing attempt if it exists
                if attempt_id:
                    SubscriptionBillingAttempt.objects.filter(
                        shopify_id=attempt_id
                    ).update(
                        status='SUCCESS',
                        shopify_order_id=order_id,
                        completed_at=timezone.now()
                    )
                
                # Update subscription
                subscription.billing_cycle_count += 1
                
                # Calculate next billing date
                from dateutil.relativedelta import relativedelta
                
                interval_map = {
                    'DAY': 'days',
                    'WEEK': 'weeks',
                    'MONTH': 'months',
                    'YEAR': 'years'
                }
                
                interval_type = interval_map.get(subscription.billing_policy_interval, 'months')
                kwargs = {interval_type: subscription.billing_policy_interval_count}
                
                if subscription.next_billing_date:
                    subscription.next_billing_date = subscription.next_billing_date + relativedelta(**kwargs)
                
                subscription.save()
            
            logger.info(f"✅ Updated subscription after successful billing: {contract_id}")
            
            return JsonResponse({
                'status': 'success',
                'message': 'Billing success processed',
                'order_id': order_id
            })
            
        except CustomerSubscription.DoesNotExist:
            logger.warning(f"Subscription {contract_id} not found for billing attempt")
            return JsonResponse({'status': 'warning', 'message': 'Subscription not found'}, status=404)
        
    except Exception as e:
        logger.error(f"❌ Error handling billing success webhook: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_POST
def subscription_billing_attempt_failure_webhook(request):
    """
    Handle subscription_billing_attempts/failure webhook
    
    Fired when: Billing attempt fails
    Action: Log error, retry logic, notify customer
    """
    if not verify_shopify_webhook(request):
        return HttpResponse('Unauthorized', status=401)
    
    try:
        data = json.loads(request.body)
        
        attempt_id = data.get('admin_graphql_api_id')
        contract_id = data.get('subscription_contract_id')
        error_message = data.get('error_message', '')
        error_code = data.get('error_code', '')
        
        logger.error(f"📥 Billing attempt failed: {attempt_id} - {error_message}")
        
        # Update subscription
        try:
            subscription = CustomerSubscription.objects.get(shopify_id=contract_id)
            
            with transaction.atomic():
                # Update billing attempt
                if attempt_id:
                    SubscriptionBillingAttempt.objects.filter(
                        shopify_id=attempt_id
                    ).update(
                        status='FAILED',
                        error_message=error_message,
                        error_code=error_code,
                        completed_at=timezone.now()
                    )
                
                # Update subscription
                subscription.shopify_push_error = f"Billing failed: {error_message}"
                subscription.save()
            
            # TODO: Implement retry logic
            # TODO: Send notification to customer
            # TODO: If max retries exceeded, pause subscription
            
            logger.info(f"✅ Logged billing failure for subscription: {contract_id}")
            
            return JsonResponse({
                'status': 'success',
                'message': 'Billing failure logged',
                'error': error_message
            })
            
        except CustomerSubscription.DoesNotExist:
            logger.warning(f"Subscription {contract_id} not found for billing failure")
            return JsonResponse({'status': 'warning', 'message': 'Subscription not found'}, status=404)
        
    except Exception as e:
        logger.error(f"❌ Error handling billing failure webhook: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_POST
def customer_payment_method_create_webhook(request):
    """
    Handle customer_payment_methods/create webhook
    
    Fired when: Customer adds a payment method
    Action: Link payment method to subscriptions
    """
    if not verify_shopify_webhook(request):
        return HttpResponse('Unauthorized', status=401)
    
    try:
        data = json.loads(request.body)
        
        payment_method_id = data.get('admin_graphql_api_id')
        customer_id = data.get('customer_id')  # Numeric ID
        customer_gid = f"gid://shopify/Customer/{customer_id}"
        
        logger.info(f"📥 New payment method added: {payment_method_id}")
        
        # Find customer
        try:
            customer = ShopifyCustomer.objects.get(shopify_id=customer_gid)
            
            # Update subscriptions without payment methods
            subscriptions = CustomerSubscription.objects.filter(
                customer=customer,
                payment_method_id__in=['', None],
                status='ACTIVE'
            )
            
            count = subscriptions.update(payment_method_id=payment_method_id)
            
            logger.info(f"✅ Linked payment method to {count} subscriptions")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Linked payment method to {count} subscriptions'
            })
            
        except ShopifyCustomer.DoesNotExist:
            logger.warning(f"Customer {customer_gid} not found")
            return JsonResponse({'status': 'warning', 'message': 'Customer not found'}, status=404)
        
    except Exception as e:
        logger.error(f"❌ Error handling payment method create webhook: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_POST
def customer_payment_method_revoke_webhook(request):
    """
    Handle customer_payment_methods/revoke webhook
    
    Fired when: Payment method is revoked (expired, removed, etc.)
    Action: Clear payment method from subscriptions, notify customer
    """
    if not verify_shopify_webhook(request):
        return HttpResponse('Unauthorized', status=401)
    
    try:
        data = json.loads(request.body)
        
        payment_method_id = data.get('admin_graphql_api_id')
        
        logger.warning(f"📥 Payment method revoked: {payment_method_id}")
        
        # Find subscriptions using this payment method
        subscriptions = CustomerSubscription.objects.filter(
            payment_method_id=payment_method_id,
            status='ACTIVE'
        )
        
        count = 0
        for subscription in subscriptions:
            subscription.payment_method_id = ''
            subscription.status = 'PAUSED'  # Pause until customer adds new payment
            subscription.shopify_push_error = "Payment method revoked - customer must add new payment method"
            subscription.save()
            count += 1
            
            # TODO: Send email to customer to add new payment method
            logger.warning(f"⚠️ Paused subscription {subscription.id} due to revoked payment")
        
        logger.info(f"✅ Paused {count} subscriptions due to revoked payment method")
        
        return JsonResponse({
            'status': 'success',
            'message': f'Paused {count} subscriptions',
            'action_required': 'customer_must_add_payment'
        })
        
    except Exception as e:
        logger.error(f"❌ Error handling payment method revoke webhook: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# Webhook URL mappings
WEBHOOK_HANDLERS = {
    'subscription_contracts/create': subscription_contract_create_webhook,
    'subscription_contracts/update': subscription_contract_update_webhook,
    'subscription_billing_attempts/success': subscription_billing_attempt_success_webhook,
    'subscription_billing_attempts/failure': subscription_billing_attempt_failure_webhook,
    'customer_payment_methods/create': customer_payment_method_create_webhook,
    'customer_payment_methods/revoke': customer_payment_method_revoke_webhook,
}




