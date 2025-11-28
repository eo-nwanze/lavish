import json
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.core.management import call_command
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .client import ShopifyAPIClient, ShopifyWebhookHandler
from .models import ShopifyStore, SyncOperation
from customers.services import CustomerSyncService

logger = logging.getLogger('shopify_integration')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_connection(request):
    """Test Shopify API connection"""
    try:
        client = ShopifyAPIClient()
        success = client.test_connection()
        
        if success:
            return Response({
                'status': 'success',
                'message': 'Successfully connected to Shopify API',
                'store_domain': client.store_domain
            })
        else:
            return Response({
                'status': 'error',
                'message': 'Failed to connect to Shopify API'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_data(request):
    """Trigger data synchronization"""
    sync_type = request.data.get('type', 'all')
    store_domain = request.data.get('store_domain')
    
    try:
        # Run sync command asynchronously (in production, use Celery)
        call_command('sync_shopify_data', type=sync_type, store=store_domain)
        
        return Response({
            'status': 'success',
            'message': f'Synchronization started for: {sync_type}'
        })
        
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@require_http_methods(["POST"])
def webhook_handler(request):
    """Handle Shopify webhooks"""
    try:
        # Get webhook topic from headers
        topic = request.META.get('HTTP_X_SHOPIFY_TOPIC')
        if not topic:
            return HttpResponse('Missing webhook topic', status=400)
        
        # Verify webhook authenticity
        webhook_handler = ShopifyWebhookHandler()
        if not webhook_handler.verify_webhook(request):
            logger.warning('Invalid webhook signature')
            return HttpResponse('Invalid signature', status=401)
        
        # Parse webhook data
        try:
            data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return HttpResponse('Invalid JSON', status=400)
        
        # Handle webhook
        success = webhook_handler.handle_webhook(topic, data)
        
        if success:
            logger.info(f'Successfully handled webhook: {topic}')
            return HttpResponse('OK')
        else:
            logger.error(f'Failed to handle webhook: {topic}')
            return HttpResponse('Processing failed', status=500)
            
    except Exception as e:
        logger.error(f'Webhook handler error: {e}')
        return HttpResponse('Internal error', status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def store_list(request):
    """List configured Shopify stores"""
    stores = ShopifyStore.objects.all()
    data = []
    
    for store in stores:
        data.append({
            'id': store.id,
            'store_domain': store.store_domain,
            'store_name': store.store_name,
            'currency': store.currency,
            'timezone': store.timezone,
            'is_active': store.is_active,
            'last_sync': store.last_sync,
            'created_at': store.created_at,
        })
    
    return Response({'stores': data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sync_operations_list(request):
    """List recent sync operations"""
    operations = SyncOperation.objects.all()[:20]  # Last 20 operations
    data = []
    
    for op in operations:
        data.append({
            'id': op.id,
            'operation_type': op.operation_type,
            'status': op.status,
            'total_records': op.total_records,
            'processed_records': op.processed_records,
            'created_records': op.created_records,
            'updated_records': op.updated_records,
            'error_records': op.error_records,
            'progress_percentage': op.progress_percentage,
            'started_at': op.started_at,
            'completed_at': op.completed_at,
            'error_message': op.error_message,
        })
    
    return Response({'operations': data})
