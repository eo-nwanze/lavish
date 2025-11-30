import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.utils import timezone
from .models import ShopifyStore, APIRateLimit, SyncOperation
import logging

logger = logging.getLogger('shopify_integration')


class ShopifyAPIClient:
    """
    Enhanced Shopify API client based on proven 7fa66cac patterns
    Supports real-time data synchronization with pagination and error handling
    """
    
    def __init__(self, store_domain=None, access_token=None, api_version=None):
        self.store_domain = store_domain or settings.SHOPIFY_STORE_URL
        self.access_token = access_token or settings.SHOPIFY_ACCESS_TOKEN
        self.api_version = api_version or settings.SHOPIFY_API_VERSION
        
        # API endpoints
        self.graphql_endpoint = f"https://{self.store_domain}/admin/api/{self.api_version}/graphql.json"
        self.rest_endpoint = f"https://{self.store_domain}/admin/api/{self.api_version}"
        
        # Rate limiting
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        
        logger.info(f"Initialized Shopify API client for {self.store_domain}")
    
    def _get_headers(self):
        """Get standard headers for API requests"""
        return {
            'Content-Type': 'application/json',
            'X-Shopify-Access-Token': self.access_token
        }
    
    def _handle_rate_limit(self, response):
        """Handle rate limiting based on response headers"""
        if 'X-Shopify-Shop-Api-Call-Limit' in response.headers:
            call_limit = response.headers['X-Shopify-Shop-Api-Call-Limit']
            current_calls, max_calls = map(int, call_limit.split('/'))
            
            # Update rate limit tracking
            try:
                store = ShopifyStore.objects.get(store_domain=self.store_domain)
                rate_limit, created = APIRateLimit.objects.get_or_create(
                    store=store,
                    api_type='rest',
                    defaults={
                        'window_start': timezone.now(),
                        'window_end': timezone.now() + timedelta(seconds=1),
                    }
                )
                rate_limit.current_calls = current_calls
                rate_limit.max_calls = max_calls
                rate_limit.is_throttled = current_calls >= max_calls * 0.8  # 80% threshold
                rate_limit.save()
                
                # If approaching limit, add delay
                if current_calls >= max_calls * 0.8:
                    time.sleep(0.5)
                    
            except ShopifyStore.DoesNotExist:
                logger.warning(f"Store {self.store_domain} not found in database")
    
    def execute_graphql_query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """Execute GraphQL query with enhanced error handling and rate limiting"""
        # Rate limiting is handled after the request via _handle_rate_limit()
        
        headers = {
            'Content-Type': 'application/json',
            'X-Shopify-Access-Token': self.access_token,
            'Accept': 'application/json'
        }
        
        payload = {'query': query}
        if variables:
            payload['variables'] = variables
        
        try:
            response = requests.post(
                self.graphql_endpoint,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            # Update rate limit info
            self._handle_rate_limit(response)
            
            if response.status_code != 200:
                logger.error(f"GraphQL request failed: {response.status_code} - {response.text}")
                return {"error": f"HTTP {response.status_code}: {response.text}"}
            
            result = response.json()
            
            # Check for GraphQL errors
            if 'errors' in result:
                logger.error(f"GraphQL errors: {result['errors']}")
                return result
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"GraphQL request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise
        
        return {'error': 'Max retries exceeded'}
    
    def rest_request(self, method, endpoint, data=None, params=None):
        """Execute a REST API request"""
        url = f"{self.rest_endpoint}/{endpoint.lstrip('/')}"
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"REST {method} attempt {attempt + 1}: {url}")
                
                response = requests.request(
                    method,
                    url,
                    headers=self._get_headers(),
                    json=data,
                    params=params,
                    timeout=30
                )
                
                self._handle_rate_limit(response)
                
                if response.status_code in [200, 201, 204]:
                    if response.content:
                        return response.json()
                    return {'success': True}
                
                elif response.status_code == 429:  # Rate limited
                    retry_after = int(response.headers.get('Retry-After', self.retry_delay))
                    logger.warning(f"Rate limited, waiting {retry_after} seconds")
                    time.sleep(retry_after)
                    continue
                
                else:
                    logger.error(f"HTTP {response.status_code}: {response.text}")
                    return {'error': f"HTTP {response.status_code}: {response.text}"}
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    return {'error': str(e)}
        
        return {'error': 'Max retries exceeded'}
    
    # Customer API methods
    def get_customers(self, limit=50, cursor=None):
        """
        Get customers using GraphQL pagination
        Based on shopify_admin_customer_puller.py
        """
        query = """
        query GetCustomers($first: Int!, $after: String) {
            customers(first: $first, after: $after) {
                pageInfo {
                    hasNextPage
                    endCursor
                }
                nodes {
                    id
                    firstName
                    lastName
                    email
                    phone
                    createdAt
                    updatedAt
                    numberOfOrders
                    state
                    verifiedEmail
                    taxExempt
                    tags
                    addresses {
                        id
                        firstName
                        lastName
                        company
                        address1
                        address2
                        city
                        province
                        country
                        zip
                        phone
                        provinceCode
                        countryCode
                        countryName
                    }
                }
            }
        }
        """
        
        variables = {'first': limit}
        if cursor:
            variables['after'] = cursor
        
        return self.graphql_query(query, variables)
    
    def get_customer(self, customer_id):
        """Get a single customer by ID"""
        query = """
        query GetCustomer($id: ID!) {
            customer(id: $id) {
                id
                firstName
                lastName
                email
                phone
                createdAt
                updatedAt
                numberOfOrders
                state
                verifiedEmail
                taxExempt
                tags
                note
                lifetimeDuration
                validEmailAddress
                image {
                    url
                    altText
                }
                addresses {
                    id
                    firstName
                    lastName
                    company
                    address1
                    address2
                    city
                    province
                    country
                    zip
                    phone
                    provinceCode
                    countryCode
                    countryName
                    formattedArea
                }
            }
        }
        """
        
        return self.graphql_query(query, {'id': customer_id})
    
    # Product API methods
    def get_products(self, limit=50, cursor=None):
        """Get products using GraphQL pagination"""
        query = """
        query GetProducts($first: Int!, $after: String) {
            products(first: $first, after: $after) {
                pageInfo {
                    hasNextPage
                    endCursor
                }
                nodes {
                    id
                    title
                    handle
                    description
                    productType
                    vendor
                    status
                    publishedAt
                    createdAt
                    updatedAt
                    tags
                    seo {
                        title
                        description
                    }
                    variants(first: 100) {
                        nodes {
                            id
                            title
                            sku
                            barcode
                            price
                            compareAtPrice
                            inventoryQuantity
                            inventoryPolicy
                            weight
                            weightUnit
                            availableForSale
                            requiresShipping
                            taxable
                            position
                            createdAt
                            updatedAt
                        }
                    }
                    images(first: 20) {
                        nodes {
                            id
                            url
                            altText
                            width
                            height
                            position
                        }
                    }
                }
            }
        }
        """
        
        variables = {'first': limit}
        if cursor:
            variables['after'] = cursor
        
        return self.graphql_query(query, variables)
    
    # Inventory API methods
    def get_inventory_items(self, limit=50, cursor=None):
        """Get inventory items"""
        query = """
        query GetInventoryItems($first: Int!, $after: String) {
            inventoryItems(first: $first, after: $after) {
                pageInfo {
                    hasNextPage
                    endCursor
                }
                nodes {
                    id
                    sku
                    tracked
                    requiresShipping
                    createdAt
                    updatedAt
                    inventoryLevels(first: 10) {
                        nodes {
                            id
                            available
                            location {
                                id
                                name
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {'first': limit}
        if cursor:
            variables['after'] = cursor
        
        return self.graphql_query(query, variables)
    
    # Order API methods
    def get_orders(self, limit=50, cursor=None):
        """Get orders using GraphQL pagination"""
        query = """
        query GetOrders($first: Int!, $after: String) {
            orders(first: $first, after: $after) {
                pageInfo {
                    hasNextPage
                    endCursor
                }
                nodes {
                    id
                    name
                    email
                    phone
                    createdAt
                    updatedAt
                    processedAt
                    financialStatus
                    fulfillmentStatus
                    totalPrice
                    subtotalPrice
                    totalTax
                    totalShippingPrice
                    currencyCode
                    customer {
                        id
                        email
                        firstName
                        lastName
                    }
                    lineItems(first: 100) {
                        nodes {
                            id
                            title
                            quantity
                            variant {
                                id
                                sku
                                title
                            }
                            product {
                                id
                                title
                            }
                        }
                    }
                    shippingAddress {
                        firstName
                        lastName
                        company
                        address1
                        address2
                        city
                        province
                        country
                        zip
                        phone
                    }
                    billingAddress {
                        firstName
                        lastName
                        company
                        address1
                        address2
                        city
                        province
                        country
                        zip
                        phone
                    }
                }
            }
        }
        """
        
        variables = {'first': limit}
        if cursor:
            variables['after'] = cursor
        
        return self.graphql_query(query, variables)
    
    def test_connection(self):
        """Test API connection"""
        query = """
        query {
            shop {
                name
                email
                domain
                currencyCode
                timezone
            }
        }
        """
        
        result = self.graphql_query(query)
        if 'error' not in result and 'data' in result:
            logger.info(f"Successfully connected to {result['data']['shop']['name']}")
            return True
        else:
            logger.error(f"Connection test failed: {result}")
            return False


class ShopifyWebhookHandler:
    """Handle incoming Shopify webhooks"""
    
    def __init__(self, webhook_secret=None):
        self.webhook_secret = webhook_secret or settings.SHOPIFY_API_SECRET
    
    def verify_webhook(self, request):
        """Verify webhook authenticity"""
        import hmac
        import hashlib
        import base64
        
        if 'HTTP_X_SHOPIFY_HMAC_SHA256' not in request.META:
            return False
        
        hmac_header = request.META['HTTP_X_SHOPIFY_HMAC_SHA256']
        body = request.body
        
        calculated_hmac = base64.b64encode(
            hmac.new(
                self.webhook_secret.encode('utf-8'),
                body,
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
        return hmac.compare_digest(calculated_hmac, hmac_header)
    
    def handle_webhook(self, topic, data):
        """Handle webhook based on topic"""
        logger.info(f"Handling webhook: {topic}")
        
        handlers = {
            'customers/create': self._handle_customer_create,
            'customers/update': self._handle_customer_update,
            'products/create': self._handle_product_create,
            'products/update': self._handle_product_update,
            'orders/create': self._handle_order_create,
            'orders/updated': self._handle_order_update,
        }
        
        handler = handlers.get(topic)
        if handler:
            return handler(data)
        else:
            logger.warning(f"No handler for webhook topic: {topic}")
            return False
    
    def _handle_customer_create(self, data):
        """Handle customer creation webhook"""
        # Import here to avoid circular imports
        from customers.services import CustomerSyncService
        
        service = CustomerSyncService()
        return service.sync_customer_from_webhook(data)
    
    def _handle_customer_update(self, data):
        """Handle customer update webhook"""
        from customers.services import CustomerSyncService
        
        service = CustomerSyncService()
        return service.sync_customer_from_webhook(data)
    
    def _handle_product_create(self, data):
        """Handle product creation webhook"""
        from products.services import ProductSyncService
        
        service = ProductSyncService()
        return service.sync_product_from_webhook(data)
    
    def _handle_product_update(self, data):
        """Handle product update webhook"""
        from products.services import ProductSyncService
        
        service = ProductSyncService()
        return service.sync_product_from_webhook(data)
    
    def _handle_order_create(self, data):
        """Handle order creation webhook"""
        from orders.services import OrderSyncService
        
        service = OrderSyncService()
        return service.sync_order_from_webhook(data)
    
    def _handle_order_update(self, data):
        """Handle order update webhook"""
        from orders.services import OrderSyncService
        
        service = OrderSyncService()
        return service.sync_order_from_webhook(data)
