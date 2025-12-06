"""
Subscription API Views for Shopify Theme Integration
Provides endpoints for fetching selling plans and creating subscription checkouts
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q
import logging

from .models import SellingPlan
from products.models import ShopifyProduct

logger = logging.getLogger(__name__)


@api_view(['GET'])
def get_selling_plans(request):
    """
    Get available selling plans for a product
    
    GET /api/subscriptions/selling-plans/?product_id=<product_id>
    
    Returns:
    {
        "product_id": "123456",
        "selling_plans": [
            {
                "id": 1,
                "name": "Monthly Box",
                "description": "Delivered monthly",
                "billing_policy": "RECURRING",
                "delivery_policy": "RECURRING",
                "interval_count": 1,
                "interval": "MONTH",
                "price_adjustment_type": "PERCENTAGE",
                "price_adjustment_value": 10.00,
                "is_active": true
            }
        ]
    }
    """
    try:
        product_id = request.GET.get('product_id')
        
        if not product_id:
            return Response({
                'error': 'product_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get product to verify it exists
        try:
            product = ShopifyProduct.objects.get(shopify_product_id=product_id)
        except ShopifyProduct.DoesNotExist:
            return Response({
                'error': f'Product with id {product_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get active selling plans
        # For now, return all active plans - you can add product-specific filtering later
        selling_plans = SellingPlan.objects.filter(
            is_active=True
        ).order_by('interval_count', 'interval')
        
        plans_data = []
        for plan in selling_plans:
            plan_data = {
                'id': plan.id,
                'name': plan.name,
                'description': plan.description or '',
                'billing_policy': plan.billing_policy,
                'delivery_policy': plan.delivery_policy,
                'interval_count': plan.billing_interval_count,
                'interval': plan.billing_interval,
                'price_adjustment_type': plan.price_adjustment_type,
                'price_adjustment_value': float(plan.price_adjustment_value) if plan.price_adjustment_value else 0,
                'is_active': plan.is_active,
                'cutoff_days_before_delivery': plan.cutoff_days_before_delivery,
            }
            plans_data.append(plan_data)
        
        return Response({
            'product_id': product_id,
            'product_name': product.title,
            'selling_plans': plans_data
        })
    
    except Exception as e:
        logger.error(f"Error fetching selling plans: {str(e)}")
        return Response({
            'error': 'An error occurred while fetching selling plans',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def create_subscription_checkout(request):
    """
    Create a subscription checkout session
    
    POST /api/subscriptions/checkout/create/
    Body:
    {
        "customer_id": "123456",
        "selling_plan_id": 1,
        "variant_id": "gid://shopify/ProductVariant/...",
        "quantity": 1
    }
    
    Returns:
    {
        "checkout_url": "https://...",
        "subscription_id": 123
    }
    """
    try:
        customer_id = request.data.get('customer_id')
        selling_plan_id = request.data.get('selling_plan_id')
        variant_id = request.data.get('variant_id')
        quantity = request.data.get('quantity', 1)
        
        # Validate required fields
        if not all([customer_id, selling_plan_id, variant_id]):
            return Response({
                'error': 'customer_id, selling_plan_id, and variant_id are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify selling plan exists
        try:
            selling_plan = SellingPlan.objects.get(id=selling_plan_id, is_active=True)
        except SellingPlan.DoesNotExist:
            return Response({
                'error': f'Selling plan with id {selling_plan_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # TODO: Implement Shopify checkout creation
        # This would create a subscription contract draft in Shopify
        # and return a checkout URL for the customer
        
        logger.info(f"Subscription checkout requested - Customer: {customer_id}, Plan: {selling_plan_id}, Variant: {variant_id}")
        
        return Response({
            'message': 'Subscription checkout creation is not yet implemented',
            'selling_plan': {
                'id': selling_plan.id,
                'name': selling_plan.name,
                'interval': f"{selling_plan.billing_interval_count} {selling_plan.billing_interval}"
            },
            'customer_id': customer_id,
            'variant_id': variant_id,
            'quantity': quantity
        }, status=status.HTTP_501_NOT_IMPLEMENTED)
    
    except Exception as e:
        logger.error(f"Error creating subscription checkout: {str(e)}")
        return Response({
            'error': 'An error occurred while creating subscription checkout',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
