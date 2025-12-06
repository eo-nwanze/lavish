"""
Subscription Payment API Views
Django REST API endpoints for managing subscriptions with Shopify payment methods
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import CustomerSubscription, SellingPlan
from .shopify_payment_service import ShopifyPaymentMethodService
from customers.models import ShopifyCustomer
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_customer_payment_methods(request, customer_id):
    """
    Get all saved payment methods for a customer from Shopify
    
    GET /api/subscriptions/customers/<customer_id>/payment-methods/
    """
    try:
        # Verify customer exists
        customer = get_object_or_404(ShopifyCustomer, shopify_id=customer_id)
        
        # Get payment methods from Shopify
        payment_service = ShopifyPaymentMethodService()
        customer_data = payment_service.get_customer_payment_methods(customer_id)
        
        if not customer_data:
            return Response({
                'error': 'Unable to fetch payment methods'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Format payment methods for response
        payment_methods = customer_data.get('paymentMethods', {}).get('edges', [])
        formatted_methods = []
        
        for edge in payment_methods:
            method = edge['node']
            formatted_method = {
                'id': method['id'],
                'type': method.get('instrument', 'unknown')
            }
            
            # Add card details if it's a credit card
            if 'brand' in method:
                formatted_method.update({
                    'brand': method.get('brand'),
                    'last_digits': method.get('lastDigits'),
                    'expiry_month': method.get('expiryMonth'),
                    'expiry_year': method.get('expiryYear'),
                    'masked_number': method.get('maskedNumber')
                })
            
            formatted_methods.append(formatted_method)
        
        return Response({
            'customer': {
                'id': customer_data['id'],
                'name': customer_data.get('displayName'),
                'email': customer_data.get('email')
            },
            'payment_methods': formatted_methods
        })
    
    except Exception as e:
        logger.error(f"Error fetching payment methods: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_subscription_with_saved_payment(request):
    """
    Create a subscription using customer's saved Shopify payment method
    
    POST /api/subscriptions/create-with-payment/
    Body:
    {
        "customer_id": "123456",
        "selling_plan_id": 1,
        "payment_method_id": "gid://shopify/CustomerPaymentMethod/...",
        "line_items": [
            {
                "variant_id": "gid://shopify/ProductVariant/...",
                "quantity": 1,
                "price": "29.99"
            }
        ],
        "delivery_address": {...} // Optional
    }
    """
    try:
        data = request.data
        
        # Validate required fields
        required_fields = ['customer_id', 'selling_plan_id', 'payment_method_id', 'line_items']
        for field in required_fields:
            if field not in data:
                return Response({
                    'error': f'Missing required field: {field}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get customer
        customer = get_object_or_404(ShopifyCustomer, shopify_id=data['customer_id'])
        
        # Get selling plan
        selling_plan = get_object_or_404(SellingPlan, id=data['selling_plan_id'])
        
        # Prepare subscription details for Shopify
        selling_plan_details = {
            'billing_interval': selling_plan.billing_interval,
            'billing_interval_count': selling_plan.billing_interval_count,
            'delivery_interval': selling_plan.delivery_interval,
            'delivery_interval_count': selling_plan.delivery_interval_count,
            'line_items': data['line_items'],
            'currency': data.get('currency', 'USD')
        }
        
        # Add next billing date if provided
        if data.get('next_billing_date'):
            selling_plan_details['next_billing_date'] = data['next_billing_date']
        
        # Create subscription contract in Shopify
        payment_service = ShopifyPaymentMethodService()
        result = payment_service.create_subscription_contract_with_payment(
            customer_id=data['customer_id'],
            payment_method_id=data['payment_method_id'],
            selling_plan_details=selling_plan_details,
            delivery_address=data.get('delivery_address')
        )
        
        if not result.get('success'):
            return Response({
                'error': 'Failed to create subscription in Shopify',
                'details': result.get('errors')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create subscription record in Django
        contract = result['contract']
        subscription = CustomerSubscription.objects.create(
            shopify_id=contract['id'],
            customer=customer,
            selling_plan=selling_plan,
            status=contract['status'],
            payment_method_id=data['payment_method_id'],
            next_billing_date=contract.get('nextBillingDate'),
            billing_policy_interval=selling_plan.billing_interval,
            billing_policy_interval_count=selling_plan.billing_interval_count,
            delivery_policy_interval=selling_plan.delivery_interval,
            delivery_policy_interval_count=selling_plan.delivery_interval_count,
            line_items=data['line_items'],
            delivery_address=data.get('delivery_address', {}),
            created_in_django=True,
            contract_created_at=timezone.now()
        )
        
        # Calculate total price from line items
        total = sum(float(item['price']) * item.get('quantity', 1) for item in data['line_items'])
        subscription.total_price = total
        subscription.save()
        
        return Response({
            'success': True,
            'subscription': {
                'id': subscription.id,
                'shopify_id': subscription.shopify_id,
                'status': subscription.status,
                'next_billing_date': subscription.next_billing_date,
                'total_price': str(subscription.total_price)
            }
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        logger.error(f"Error creating subscription: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_subscription_payment_method(request, subscription_id):
    """
    Update payment method for an existing subscription
    
    PUT /api/subscriptions/<subscription_id>/payment-method/
    Body:
    {
        "payment_method_id": "gid://shopify/CustomerPaymentMethod/..."
    }
    """
    try:
        subscription = get_object_or_404(CustomerSubscription, id=subscription_id)
        
        new_payment_method_id = request.data.get('payment_method_id')
        if not new_payment_method_id:
            return Response({
                'error': 'payment_method_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update in Shopify
        payment_service = ShopifyPaymentMethodService()
        result = payment_service.update_subscription_payment_method(
            subscription.shopify_id,
            new_payment_method_id
        )
        
        if result.get('userErrors'):
            return Response({
                'error': 'Failed to update payment method',
                'details': result['userErrors']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update in Django
        subscription.payment_method_id = new_payment_method_id
        subscription.save()
        
        return Response({
            'success': True,
            'message': 'Payment method updated successfully'
        })
    
    except Exception as e:
        logger.error(f"Error updating payment method: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_payment_method(request):
    """
    Verify if a payment method is still valid
    
    GET /api/subscriptions/verify-payment-method/?payment_method_id=...
    """
    try:
        payment_method_id = request.query_params.get('payment_method_id')
        if not payment_method_id:
            return Response({
                'error': 'payment_method_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        payment_service = ShopifyPaymentMethodService()
        is_valid = payment_service.verify_payment_method_active(payment_method_id)
        
        return Response({
            'payment_method_id': payment_method_id,
            'is_valid': is_valid
        })
    
    except Exception as e:
        logger.error(f"Error verifying payment method: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
