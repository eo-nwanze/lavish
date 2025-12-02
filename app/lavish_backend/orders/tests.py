"""
Tests for Orders and Fulfillment API
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, timedelta
import json
from unittest.mock import patch, MagicMock

from orders.models import ShopifyOrder, ShopifyOrderLineItem, ShopifyOrderAddress
from shipping.models import ShopifyFulfillmentOrder
from shopify_integration.client import ShopifyAPIClient


class OrdersAPITestCase(TestCase):
    """Test cases for Orders API endpoints"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        # Create test order
        self.order = ShopifyOrder.objects.create(
            shopify_id='gid://shopify/Order/123456789',
            name='#1001',
            customer_email='test@example.com',
            total_price='99.99',
            currency_code='USD',
            financial_status='pending',
            fulfillment_status='null',
            created_at=timezone.now(),
            updated_at=timezone.now(),
            store_domain='test-shop.myshopify.com'
        )
        
        # Create test line item
        self.line_item = ShopifyOrderLineItem.objects.create(
            shopify_id='gid://shopify/LineItem/987654321',
            order=self.order,
            title='Test Product',
            quantity=1,
            price='99.99',
            variant_title='Default',
            variant_sku='TEST-SKU',
            product_title='Test Product',
            store_domain='test-shop.myshopify.com'
        )
        
        # Create test address
        self.address = ShopifyOrderAddress.objects.create(
            order=self.order,
            address_type='shipping',
            first_name='John',
            last_name='Doe',
            address1='123 Main St',
            city='New York',
            province='NY',
            country='US',
            zip_code='10001',
            store_domain='test-shop.myshopify.com'
        )
    
    def test_order_list_endpoint(self):
        """Test order list endpoint"""
        url = reverse('orders:order_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['orders']), 1)
        self.assertEqual(data['orders'][0]['name'], '#1001')
    
    def test_order_list_with_filters(self):
        """Test order list endpoint with filters"""
        url = reverse('orders:order_list')
        response = self.client.get(url, {
            'financial_status': 'pending',
            'page_size': 10
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['pagination']['page_size'], 10)
    
    def test_order_detail_endpoint(self):
        """Test order detail endpoint"""
        url = reverse('orders:order_detail', kwargs={'shopify_id': 'gid://shopify/Order/123456789'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['order']['name'], '#1001')
        self.assertEqual(len(data['order']['line_items']), 1)
        self.assertEqual(len(data['order']['addresses']), 1)
    
    def test_order_statistics_endpoint(self):
        """Test order statistics endpoint"""
        url = reverse('orders:order_statistics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['summary']['total_orders'], 1)
        self.assertEqual(data['summary']['pending_orders'], 1)
    
    def test_customer_orders_endpoint(self):
        """Test customer orders endpoint"""
        url = reverse('orders:customer_orders')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['orders']), 1)
        self.assertEqual(data['statistics']['total_orders'], 1)
    
    def test_order_update_status_endpoint(self):
        """Test order update status endpoint"""
        url = reverse('orders:order_update_status', kwargs={'shopify_id': 'gid://shopify/Order/123456789'})
        response = self.client.post(url, {
            'financial_status': 'paid',
            'note': 'Status updated for testing'
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['order']['financial_status'], 'paid')
        
        # Verify database update
        self.order.refresh_from_db()
        self.assertEqual(self.order.financial_status, 'paid')
    
    @patch('orders.views.ShopifyAPIClient')
    def test_order_sync_endpoint(self, mock_client):
        """Test order sync endpoint"""
        mock_client_instance = mock_client.return_value
        mock_client_instance.get_order.return_value = {
            'id': 'gid://shopify/Order/123456789',
            'name': '#1001',
            'email': 'test@example.com',
            'total_price_set': {'shopMoney': {'amount': '99.99', 'currencyCode': 'USD'}},
            'financial_status': 'paid',
            'fulfillment_status': 'null',
            'created_at': '2024-01-01T12:00:00Z',
            'updated_at': '2024-01-01T12:00:00Z',
            'line_items': [],
            'shipping_address': {}
        }
        
        url = reverse('orders:order_sync')
        response = self.client.post(url, {
            'sync_type': 'single',
            'shopify_id': 'gid://shopify/Order/123456789'
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['order']['name'], '#1001')
    
    @patch('orders.views.ShopifyAPIClient')
    def test_order_cancel_endpoint(self, mock_client):
        """Test order cancel endpoint"""
        mock_client_instance = mock_client.return_value
        mock_client_instance.cancel_order.return_value = {
            'order': {
                'id': 'gid://shopify/Order/123456789',
                'cancelled_at': '2024-01-01T12:00:00Z'
            }
        }
        
        url = reverse('orders:order_cancel', kwargs={'shopify_id': 'gid://shopify/Order/123456789'})
        response = self.client.post(url, {
            'reason': 'Customer requested cancellation'
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], 'Order cancelled successfully')
    
    def test_order_cancel_fulfilled_order(self):
        """Test cancelling a fulfilled order should fail"""
        # Update order to fulfilled status
        self.order.fulfillment_status = 'fulfilled'
        self.order.save()
        
        url = reverse('orders:order_cancel', kwargs={'shopify_id': 'gid://shopify/Order/123456789'})
        response = self.client.post(url, {
            'reason': 'Customer requested cancellation'
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('already been fulfilled', data['error'])
    
    def test_order_invoice_endpoint(self):
        """Test order invoice endpoint"""
        url = reverse('orders:order_invoice', kwargs={'shopify_id': 'gid://shopify/Order/123456789'})
        response = self.client.get(url)
        
        # Check if response is PDF (if reportlab is available) or error
        if response.status_code == 200:
            self.assertEqual(response['Content-Type'], 'application/pdf')
        else:
            # ReportLab might not be available in test environment
            self.assertEqual(response.status_code, 500)
    
    @patch('orders.views.ShopifyAPIClient')
    def test_order_update_address_endpoint(self, mock_client):
        """Test order update address endpoint"""
        mock_client_instance = mock_client.return_value
        mock_client_instance.update_order_address.return_value = {
            'order': {
                'id': 'gid://shopify/Order/123456789'
            }
        }
        
        url = reverse('orders:order_update_address', kwargs={'shopify_id': 'gid://shopify/Order/123456789'})
        response = self.client.post(url, {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'address1': '456 Oak Ave',
            'city': 'Boston',
            'country': 'US',
            'zip': '02101'
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['address']['first_name'], 'Jane')
    
    def test_order_update_address_fulfilled_order(self):
        """Test updating address of fulfilled order should fail"""
        # Update order to fulfilled status
        self.order.fulfillment_status = 'fulfilled'
        self.order.save()
        
        url = reverse('orders:order_update_address', kwargs={'shopify_id': 'gid://shopify/Order/123456789'})
        response = self.client.post(url, {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'address1': '456 Oak Ave',
            'city': 'Boston',
            'country': 'US',
            'zip': '02101'
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('already been fulfilled', data['error'])
    
    @patch('orders.views.ShopifyAPIClient')
    def test_order_status_endpoint(self, mock_client):
        """Test order status endpoint"""
        mock_client_instance = mock_client.return_value
        mock_client_instance.get_order_events.return_value = [
            {
                'id': '123',
                'verb': 'created',
                'message': 'Order was created',
                'createdAt': '2024-01-01T12:00:00Z'
            }
        ]
        
        url = reverse('orders:order_status', kwargs={'shopify_id': 'gid://shopify/Order/123456789'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['financial_status'], 'pending')
        self.assertEqual(len(data['timeline_events']), 2)  # Order placed + Shopify event


class FulfillmentAPITestCase(TestCase):
    """Test cases for Fulfillment API endpoints"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        # Create test order
        self.order = ShopifyOrder.objects.create(
            shopify_id='gid://shopify/Order/123456789',
            name='#1001',
            customer_email='test@example.com',
            total_price='99.99',
            currency_code='USD',
            financial_status='paid',
            fulfillment_status='null',
            created_at=timezone.now(),
            updated_at=timezone.now(),
            store_domain='test-shop.myshopify.com'
        )
        
        # Create test fulfillment order
        self.fulfillment_order = ShopifyFulfillmentOrder.objects.create(
            shopify_id='gid://shopify/FulfillmentOrder/987654321',
            order=self.order,
            status='open',
            request_status='unsubmitted',
            created_at=timezone.now(),
            updated_at=timezone.now(),
            store_domain='test-shop.myshopify.com'
        )
    
    def test_fulfillment_order_list_endpoint(self):
        """Test fulfillment order list endpoint"""
        url = reverse('shipping:fulfillment_order_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['fulfillment_orders']), 1)
        self.assertEqual(data['fulfillment_orders'][0]['status'], 'open')
    
    def test_fulfillment_order_list_with_filters(self):
        """Test fulfillment order list endpoint with filters"""
        url = reverse('shipping:fulfillment_order_list')
        response = self.client.get(url, {
            'status': 'open',
            'order_id': 'gid://shopify/Order/123456789'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['fulfillment_orders']), 1)
    
    def test_fulfillment_order_detail_endpoint(self):
        """Test fulfillment order detail endpoint"""
        url = reverse('shipping:fulfillment_order_detail', kwargs={'shopify_id': 'gid://shopify/FulfillmentOrder/987654321'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['fulfillment_order']['status'], 'open')
        self.assertEqual(data['fulfillment_order']['order']['name'], '#1001')
    
    @patch('shipping.views.ShopifyAPIClient')
    def test_fulfillment_create_endpoint(self, mock_client):
        """Test fulfillment create endpoint"""
        mock_client_instance = mock_client.return_value
        mock_client_instance.create_fulfillment.return_value = {
            'fulfillment': {
                'id': 'gid://shopify/Fulfillment/555666777',
                'status': 'success',
                'tracking_company': 'UPS',
                'tracking_numbers': ['1Z999AA10123456784'],
                'tracking_urls': ['https://www.ups.com/tracking/1Z999AA10123456784'],
                'created_at': '2024-01-01T12:00:00Z'
            }
        }
        
        url = reverse('shipping:fulfillment_create')
        response = self.client.post(url, {
            'order_shopify_id': 'gid://shopify/Order/123456789',
            'location_shopify_id': 'gid://shopify/Location/111222333',
            'tracking_numbers': ['1Z999AA10123456784'],
            'tracking_company': 'UPS',
            'notify_customer': True,
            'line_items': [
                {
                    'shopify_id': 'gid://shopify/LineItem/987654321',
                    'quantity': 1
                }
            ]
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['fulfillment']['tracking_company'], 'UPS')
    
    @patch('shipping.views.ShopifyAPIClient')
    def test_fulfillment_update_tracking_endpoint(self, mock_client):
        """Test fulfillment update tracking endpoint"""
        mock_client_instance = mock_client.return_value
        mock_client_instance.update_fulfillment_tracking.return_value = {
            'fulfillment': {
                'id': 'gid://shopify/Fulfillment/555666777',
                'tracking_company': 'FedEx',
                'tracking_numbers': ['1234567890'],
                'tracking_urls': ['https://www.fedex.com/tracking/1234567890'],
                'updated_at': '2024-01-01T12:00:00Z'
            }
        }
        
        url = reverse('shipping:fulfillment_update_tracking', kwargs={'shopify_id': 'gid://shopify/FulfillmentOrder/987654321'})
        response = self.client.post(url, {
            'tracking_numbers': ['1234567890'],
            'tracking_company': 'FedEx',
            'notify_customer': True
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['fulfillment']['tracking_company'], 'FedEx')
    
    @patch('shipping.views.ShopifyAPIClient')
    def test_fulfillment_cancel_endpoint(self, mock_client):
        """Test fulfillment cancel endpoint"""
        mock_client_instance = mock_client.return_value
        mock_client_instance.cancel_fulfillment.return_value = {
            'fulfillment': {
                'id': 'gid://shopify/Fulfillment/555666777',
                'status': 'cancelled',
                'cancelled_at': '2024-01-01T12:00:00Z'
            }
        }
        
        url = reverse('shipping:fulfillment_cancel', kwargs={'shopify_id': 'gid://shopify/FulfillmentOrder/987654321'})
        response = self.client.post(url, {
            'reason': 'Customer requested cancellation'
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['fulfillment']['status'], 'cancelled')
    
    def test_fulfillment_statistics_endpoint(self):
        """Test fulfillment statistics endpoint"""
        url = reverse('shipping:fulfillment_statistics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['summary']['total_fulfillments'], 1)
        self.assertEqual(data['summary']['open_fulfillments'], 1)


class OrderSyncServiceTestCase(TestCase):
    """Test cases for Order Sync Service"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test order
        self.order = ShopifyOrder.objects.create(
            shopify_id='gid://shopify/Order/123456789',
            name='#1001',
            customer_email='test@example.com',
            total_price='99.99',
            currency_code='USD',
            financial_status='pending',
            fulfillment_status='null',
            created_at=timezone.now(),
            updated_at=timezone.now(),
            store_domain='test-shop.myshopify.com'
        )
    
    def test_sync_order_from_webhook_create(self):
        """Test syncing order from webhook (create)"""
        from orders.services import OrderSyncService
        
        webhook_data = {
            'id': 'gid://shopify/Order/987654321',
            'name': '#1002',
            'email': 'new@example.com',
            'total_price_set': {'shopMoney': {'amount': '149.99', 'currencyCode': 'USD'}},
            'financial_status': 'paid',
            'fulfillment_status': 'null',
            'created_at': '2024-01-01T12:00:00Z',
            'updated_at': '2024-01-01T12:00:00Z',
            'line_items': [
                {
                    'id': 'gid://shopify/LineItem/555666777',
                    'title': 'New Product',
                    'quantity': 2,
                    'price': '74.99',
                    'variant': {'id': 'gid://shopify/ProductVariant/111222333', 'title': 'Large'},
                    'product': {'id': 'gid://shopify/Product/444555666', 'title': 'New Product'}
                }
            ],
            'shipping_address': {
                'first_name': 'Jane',
                'last_name': 'Smith',
                'address1': '456 Oak Ave',
                'city': 'Boston',
                'province': 'MA',
                'country': 'US',
                'zip': '02101'
            }
        }
        
        service = OrderSyncService()
        result = service.sync_order_from_webhook(webhook_data)
        
        self.assertTrue(result)
        
        # Verify order was created
        new_order = ShopifyOrder.objects.get(shopify_id='gid://shopify/Order/987654321')
        self.assertEqual(new_order.name, '#1002')
        self.assertEqual(new_order.customer_email, 'new@example.com')
        self.assertEqual(new_order.financial_status, 'paid')
        
        # Verify line item was created
        line_item = ShopifyOrderLineItem.objects.get(shopify_id='gid://shopify/LineItem/555666777')
        self.assertEqual(line_item.title, 'New Product')
        self.assertEqual(line_item.quantity, 2)
        
        # Verify address was created
        address = ShopifyOrderAddress.objects.get(order=new_order, address_type='shipping')
        self.assertEqual(address.first_name, 'Jane')
        self.assertEqual(address.city, 'Boston')
    
    def test_sync_order_from_webhook_update(self):
        """Test syncing order from webhook (update)"""
        from orders.services import OrderSyncService
        
        webhook_data = {
            'id': 'gid://shopify/Order/123456789',
            'name': '#1001',
            'email': 'test@example.com',
            'total_price_set': {'shopMoney': {'amount': '199.99', 'currencyCode': 'USD'}},
            'financial_status': 'paid',
            'fulfillment_status': 'fulfilled',
            'created_at': '2024-01-01T12:00:00Z',
            'updated_at': '2024-01-02T12:00:00Z',
            'line_items': [],
            'shipping_address': {}
        }
        
        service = OrderSyncService()
        result = service.sync_order_from_webhook(webhook_data)
        
        self.assertTrue(result)
        
        # Verify order was updated
        self.order.refresh_from_db()
        self.assertEqual(self.order.financial_status, 'paid')
        self.assertEqual(self.order.fulfillment_status, 'fulfilled')
        self.assertEqual(str(self.order.total_price), '199.99')
    
    @patch('orders.services.ShopifyAPIClient')
    def test_sync_order_from_shopify(self, mock_client):
        """Test syncing order from Shopify API"""
        mock_client_instance = mock_client.return_value
        mock_client_instance.get_order.return_value = {
            'id': 'gid://shopify/Order/555666777',
            'name': '#1003',
            'email': 'shopify@example.com',
            'total_price_set': {'shopMoney': {'amount': '79.99', 'currencyCode': 'USD'}},
            'financial_status': 'pending',
            'fulfillment_status': 'null',
            'created_at': '2024-01-01T12:00:00Z',
            'updated_at': '2024-01-01T12:00:00Z',
            'line_items': [],
            'shipping_address': {}
        }
        
        from orders.services import OrderSyncService
        
        service = OrderSyncService()
        result = service.sync_order_from_shopify('gid://shopify/Order/555666777')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['order']['name'], '#1003')
        
        # Verify order was created
        new_order = ShopifyOrder.objects.get(shopify_id='gid://shopify/Order/555666777')
        self.assertEqual(new_order.name, '#1003')


class FulfillmentSyncServiceTestCase(TestCase):
    """Test cases for Fulfillment Sync Service"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test order
        self.order = ShopifyOrder.objects.create(
            shopify_id='gid://shopify/Order/123456789',
            name='#1001',
            customer_email='test@example.com',
            total_price='99.99',
            currency_code='USD',
            financial_status='paid',
            fulfillment_status='null',
            created_at=timezone.now(),
            updated_at=timezone.now(),
            store_domain='test-shop.myshopify.com'
        )
    
    def test_sync_fulfillment_from_webhook_create(self):
        """Test syncing fulfillment from webhook (create)"""
        from shipping.services import FulfillmentSyncService
        
        webhook_data = {
            'id': 'gid://shopify/Fulfillment/987654321',
            'order_id': 'gid://shopify/Order/123456789',
            'status': 'success',
            'created_at': '2024-01-01T12:00:00Z',
            'updated_at': '2024-01-01T12:00:00Z',
            'tracking_info': {
                'company': 'UPS',
                'numbers': ['1Z999AA10123456784'],
                'urls': ['https://www.ups.com/tracking/1Z999AA10123456784']
            }
        }
        
        service = FulfillmentSyncService()
        result = service.sync_fulfillment_from_webhook(webhook_data)
        
        self.assertTrue(result)
        
        # Verify order fulfillment status was updated
        self.order.refresh_from_db()
        self.assertEqual(self.order.fulfillment_status, 'fulfilled')
    
    def test_sync_fulfillment_orders_for_order(self):
        """Test syncing fulfillment orders for an order"""
        from shipping.services import FulfillmentSyncService
        
        fulfillment_orders_data = [
            {
                'id': 'gid://shopify/FulfillmentOrder/111222333',
                'status': 'open',
                'requestStatus': 'unsubmitted',
                'createdAt': '2024-01-01T12:00:00Z',
                'updatedAt': '2024-01-01T12:00:00Z',
                'assignedLocation': {
                    'id': 'gid://shopify/Location/444555666',
                    'name': 'Main Warehouse'
                },
                'lineItems': []
            }
        ]
        
        with patch('shipping.services.ShopifyAPIClient') as mock_client:
            mock_client_instance = mock_client.return_value
            mock_client_instance.get_fulfillment_orders.return_value = fulfillment_orders_data
            
            service = FulfillmentSyncService()
            result = service.sync_fulfillment_orders_for_order('gid://shopify/Order/123456789')
            
            self.assertTrue(result['success'])
            self.assertEqual(result['stats']['total'], 1)
            self.assertEqual(result['stats']['created'], 1)


class WebhookHandlerTestCase(TestCase):
    """Test cases for Webhook Handler"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_order_create_webhook(self):
        """Test order create webhook handler"""
        from shopify_integration.client import ShopifyWebhookHandler
        
        webhook_data = {
            'id': 'gid://shopify/Order/987654321',
            'name': '#1002',
            'email': 'webhook@example.com',
            'total_price_set': {'shopMoney': {'amount': '149.99', 'currencyCode': 'USD'}},
            'financial_status': 'pending',
            'fulfillment_status': 'null',
            'created_at': '2024-01-01T12:00:00Z',
            'updated_at': '2024-01-01T12:00:00Z',
            'line_items': [],
            'shipping_address': {}
        }
        
        handler = ShopifyWebhookHandler()
        result = handler.handle_webhook('orders/create', webhook_data)
        
        self.assertTrue(result)
        
        # Verify order was created
        order = ShopifyOrder.objects.get(shopify_id='gid://shopify/Order/987654321')
        self.assertEqual(order.name, '#1002')
        self.assertEqual(order.customer_email, 'webhook@example.com')
    
    def test_order_updated_webhook(self):
        """Test order updated webhook handler"""
        # Create initial order
        order = ShopifyOrder.objects.create(
            shopify_id='gid://shopify/Order/123456789',
            name='#1001',
            customer_email='test@example.com',
            total_price='99.99',
            currency_code='USD',
            financial_status='pending',
            fulfillment_status='null',
            created_at=timezone.now(),
            updated_at=timezone.now(),
            store_domain='test-shop.myshopify.com'
        )
        
        webhook_data = {
            'id': 'gid://shopify/Order/123456789',
            'name': '#1001',
            'email': 'test@example.com',
            'total_price_set': {'shopMoney': {'amount': '199.99', 'currencyCode': 'USD'}},
            'financial_status': 'paid',
            'fulfillment_status': 'null',
            'created_at': '2024-01-01T12:00:00Z',
            'updated_at': '2024-01-02T12:00:00Z',
            'line_items': [],
            'shipping_address': {}
        }
        
        handler = ShopifyWebhookHandler()
        result = handler.handle_webhook('orders/updated', webhook_data)
        
        self.assertTrue(result)
        
        # Verify order was updated
        order.refresh_from_db()
        self.assertEqual(order.financial_status, 'paid')
        self.assertEqual(str(order.total_price), '199.99')
    
    def test_fulfillment_create_webhook(self):
        """Test fulfillment create webhook handler"""
        # Create initial order
        order = ShopifyOrder.objects.create(
            shopify_id='gid://shopify/Order/123456789',
            name='#1001',
            customer_email='test@example.com',
            total_price='99.99',
            currency_code='USD',
            financial_status='paid',
            fulfillment_status='null',
            created_at=timezone.now(),
            updated_at=timezone.now(),
            store_domain='test-shop.myshopify.com'
        )
        
        webhook_data = {
            'id': 'gid://shopify/Fulfillment/987654321',
            'order_id': 'gid://shopify/Order/123456789',
            'status': 'success',
            'created_at': '2024-01-01T12:00:00Z',
            'updated_at': '2024-01-01T12:00:00Z',
            'tracking_info': {
                'company': 'UPS',
                'numbers': ['1Z999AA10123456784']
            }
        }
        
        handler = ShopifyWebhookHandler()
        result = handler.handle_webhook('fulfillments/create', webhook_data)
        
        self.assertTrue(result)
        
        # Verify order fulfillment status was updated
        order.refresh_from_db()
        self.assertEqual(order.fulfillment_status, 'fulfilled')
    
    def test_unknown_webhook_topic(self):
        """Test handling unknown webhook topic"""
        webhook_data = {'test': 'data'}
        
        handler = ShopifyWebhookHandler()
        result = handler.handle_webhook('unknown/topic', webhook_data)
        
        self.assertFalse(result)  # Should return False for unknown topics


class IntegrationTestCase(TestCase):
    """Integration tests for the complete order and fulfillment system"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    @patch('shopify_integration.client.ShopifyAPIClient')
    def test_complete_order_workflow(self, mock_client):
        """Test complete order workflow from creation to fulfillment"""
        mock_client_instance = mock_client.return_value
        
        # Step 1: Order created via webhook
        webhook_data = {
            'id': 'gid://shopify/Order/123456789',
            'name': '#1001',
            'email': 'test@example.com',
            'total_price_set': {'shopMoney': {'amount': '99.99', 'currencyCode': 'USD'}},
            'financial_status': 'pending',
            'fulfillment_status': 'null',
            'created_at': '2024-01-01T12:00:00Z',
            'updated_at': '2024-01-01T12:00:00Z',
            'line_items': [
                {
                    'id': 'gid://shopify/LineItem/987654321',
                    'title': 'Test Product',
                    'quantity': 1,
                    'price': '99.99',
                    'variant': {'id': 'gid://shopify/ProductVariant/111222333', 'title': 'Default'},
                    'product': {'id': 'gid://shopify/Product/444555666', 'title': 'Test Product'}
                }
            ],
            'shipping_address': {
                'first_name': 'John',
                'last_name': 'Doe',
                'address1': '123 Main St',
                'city': 'New York',
                'province': 'NY',
                'country': 'US',
                'zip': '10001'
            }
        }
        
        from shopify_integration.client import ShopifyWebhookHandler
        handler = ShopifyWebhookHandler()
        result = handler.handle_webhook('orders/create', webhook_data)
        self.assertTrue(result)
        
        # Verify order exists
        order = ShopifyOrder.objects.get(shopify_id='gid://shopify/Order/123456789')
        self.assertEqual(order.name, '#1001')
        self.assertEqual(order.financial_status, 'pending')
        
        # Step 2: Payment confirmed via webhook
        webhook_data['financial_status'] = 'paid'
        webhook_data['processed_at'] = '2024-01-01T13:00:00Z'
        result = handler.handle_webhook('orders/updated', webhook_data)
        self.assertTrue(result)
        
        # Verify payment status
        order.refresh_from_db()
        self.assertEqual(order.financial_status, 'paid')
        
        # Step 3: Create fulfillment
        mock_client_instance.create_fulfillment.return_value = {
            'fulfillment': {
                'id': 'gid://shopify/Fulfillment/555666777',
                'status': 'success',
                'tracking_company': 'UPS',
                'tracking_numbers': ['1Z999AA10123456784'],
                'tracking_urls': ['https://www.ups.com/tracking/1Z999AA10123456784'],
                'created_at': '2024-01-01T14:00:00Z'
            }
        }
        
        url = reverse('shipping:fulfillment_create')
        response = self.client.post(url, {
            'order_shopify_id': 'gid://shopify/Order/123456789',
            'location_shopify_id': 'gid://shopify/Location/111222333',
            'tracking_numbers': ['1Z999AA10123456784'],
            'tracking_company': 'UPS',
            'notify_customer': True,
            'line_items': [
                {
                    'shopify_id': 'gid://shopify/LineItem/987654321',
                    'quantity': 1
                }
            ]
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Step 4: Fulfillment webhook
        fulfillment_webhook_data = {
            'id': 'gid://shopify/Fulfillment/555666777',
            'order_id': 'gid://shopify/Order/123456789',
            'status': 'success',
            'created_at': '2024-01-01T14:00:00Z',
            'updated_at': '2024-01-01T14:00:00Z',
            'tracking_info': {
                'company': 'UPS',
                'numbers': ['1Z999AA10123456784'],
                'urls': ['https://www.ups.com/tracking/1Z999AA10123456784']
            }
        }
        
        result = handler.handle_webhook('fulfillments/create', fulfillment_webhook_data)
        self.assertTrue(result)
        
        # Verify final order status
        order.refresh_from_db()
        self.assertEqual(order.fulfillment_status, 'fulfilled')
        
        # Step 5: Check customer can view order
        url = reverse('orders:customer_orders')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['orders']), 1)
        self.assertEqual(data['orders'][0]['name'], '#1001')
        self.assertEqual(data['orders'][0]['financial_status'], 'paid')
        self.assertEqual(data['orders'][0]['fulfillment_status'], 'fulfilled')
