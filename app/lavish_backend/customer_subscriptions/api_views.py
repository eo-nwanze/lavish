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
            product = ShopifyProduct.objects.get(shopify_id=product_id)
        except ShopifyProduct.DoesNotExist:
            return Response({
                'error': f'Product with id {product_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get active selling plans
        # For now, return all active plans - you can add product-specific filtering later
        selling_plans = SellingPlan.objects.filter(
            is_active=True
        ).order_by('billing_interval_count', 'billing_interval')
        
        plans_data = []
        for plan in selling_plans:
            plan_data = {
                'id': plan.id,
                'name': plan.name,
                'description': plan.description or '',
                'billing_policy': plan.billing_policy,
                'delivery_policy': plan.delivery_policy,
                'billing_interval_count': plan.billing_interval_count,
                'billing_interval': plan.billing_interval,
                'price_adjustment_type': plan.price_adjustment_type,
                'price_adjustment_value': float(plan.price_adjustment_value) if plan.price_adjustment_value else 0,
                'is_active': plan.is_active,
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
    Create a subscription checkout session using Shopify native checkout
    
    POST /api/subscriptions/checkout/create/
    Body:
    {
        "selling_plan_id": 1,
        "variant_id": "123456",  # Shopify variant ID (numeric or GID)
        "product_id": "789",     # Optional: for validation
        "quantity": 1
    }
    
    Returns:
    {
        "success": true,
        "checkout_method": "native",
        "cart_data": {
            "variant_id": "123456",
            "selling_plan": "shopify_plan_id",
            "quantity": 1
        },
        "selling_plan": {...}
    }
    """
    try:
        selling_plan_id = request.data.get('selling_plan_id')
        variant_id = request.data.get('variant_id')
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)
        
        # Validate required fields (relaxed - only need selling_plan_id and variant_id)
        if not selling_plan_id:
            return Response({
                'error': 'selling_plan_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify selling plan exists in Django
        try:
            selling_plan = SellingPlan.objects.get(id=selling_plan_id, is_active=True)
        except SellingPlan.DoesNotExist:
            return Response({
                'error': f'Selling plan with id {selling_plan_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if selling plan has been synced to Shopify
        if not selling_plan.shopify_id:
            logger.warning(f"Selling plan {selling_plan_id} not synced to Shopify yet")
            return Response({
                'error': 'This subscription plan is not yet available. Please contact support.',
                'detail': 'Selling plan not synced to Shopify'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract Shopify selling plan ID from GID
        shopify_selling_plan_id = selling_plan.shopify_id
        if 'gid://shopify/SellingPlan/' in shopify_selling_plan_id:
            shopify_selling_plan_id = shopify_selling_plan_id.split('/')[-1]
        
        logger.info(f"Subscription checkout requested - Plan: {selling_plan_id} (Shopify: {shopify_selling_plan_id}), Variant: {variant_id}, Quantity: {quantity}")
        
        # Return data for frontend to use with Shopify native checkout
        return Response({
            'success': True,
            'checkout_method': 'native',
            'cart_data': {
                'variant_id': variant_id,
                'selling_plan': shopify_selling_plan_id,
                'quantity': quantity
            },
            'selling_plan': {
                'id': selling_plan.id,
                'name': selling_plan.name,
                'shopify_id': shopify_selling_plan_id,
                'interval': f"{selling_plan.billing_interval_count} {selling_plan.billing_interval}",
                'discount': f"{selling_plan.price_adjustment_value}%" if selling_plan.price_adjustment_type == 'PERCENTAGE' else str(selling_plan.price_adjustment_value)
            },
            'message': 'Subscription data prepared for checkout'
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error creating subscription checkout: {str(e)}")
        return Response({
            'error': 'An error occurred while creating subscription checkout',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
