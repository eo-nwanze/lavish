"""
Afterpay API Client
Handles communication with Afterpay API for payment processing
"""

import requests
import base64
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from django.utils import timezone
from decimal import Decimal

logger = logging.getLogger(__name__)


class AfterpayClient:
    """
    Client for Afterpay API v2
    Handles authentication and API requests
    """
    
    def __init__(self, merchant_id: str, secret_key: str, environment: str = 'sandbox', region: str = 'US'):
        """
        Initialize Afterpay client
        
        Args:
            merchant_id: Afterpay merchant ID (username)
            secret_key: Afterpay secret key (password)
            environment: 'sandbox' or 'production'
            region: Merchant region (US, AU, NZ, CA, GB)
        """
        self.merchant_id = merchant_id
        self.secret_key = secret_key
        self.environment = environment
        self.region = region
        
        # Set base URL based on environment
        if environment == 'production':
            self.base_url = 'https://global-api.afterpay.com'
            self.portal_url = 'https://portal.afterpay.com'
        else:
            self.base_url = 'https://global-api-sandbox.afterpay.com'
            self.portal_url = 'https://portal.sandbox.afterpay.com'
        
        # Create Basic Auth header
        credentials = f"{merchant_id}:{secret_key}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.auth_header = f"Basic {encoded_credentials}"
        
        # Connection timeouts (as per Afterpay documentation)
        self.timeout_open = 10
        self.timeout_read = 20  # Default, some endpoints require 70s
        
        logger.info(f"Afterpay client initialized: {environment} environment, {region} region")
    
    def _get_headers(self, content_type: str = 'application/json') -> Dict[str, str]:
        """Get standard headers for API requests"""
        return {
            'User-Agent': 'Lavish-Library-Afterpay/1.0',
            'Authorization': self.auth_header,
            'Accept': 'application/json',
            'Content-Type': content_type,
        }
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        timeout_read: Optional[int] = None
    ) -> Dict:
        """
        Make HTTP request to Afterpay API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., '/v2/configuration')
            data: Request payload for POST requests
            timeout_read: Custom read timeout (default 20s, some endpoints need 70s)
        
        Returns:
            Response data as dictionary
        
        Raises:
            requests.exceptions.RequestException: On API errors
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        timeout = (self.timeout_open, timeout_read or self.timeout_read)
        
        logger.info(f"Afterpay API Request: {method} {url}")
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=timeout)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=data, timeout=timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Log response
            logger.info(f"Afterpay API Response: {response.status_code}")
            
            # Raise for HTTP errors
            response.raise_for_status()
            
            return response.json()
        
        except requests.exceptions.Timeout as e:
            logger.error(f"Afterpay API timeout: {e}")
            raise
        except requests.exceptions.HTTPError as e:
            logger.error(f"Afterpay API HTTP error: {e}")
            logger.error(f"Response: {e.response.text if e.response else 'No response'}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Afterpay API request error: {e}")
            raise
    
    # ====================================================================================
    # CONFIGURATION ENDPOINTS
    # ====================================================================================
    
    def get_configuration(self) -> Dict:
        """
        Get merchant configuration (payment limits)
        Should be called once per day as per Afterpay recommendation
        
        Returns:
            Dict containing minimumAmount and maximumAmount
        """
        logger.info("Fetching Afterpay configuration")
        return self._make_request('GET', '/v2/configuration')
    
    # ====================================================================================
    # CHECKOUT ENDPOINTS
    # ====================================================================================
    
    def create_checkout(
        self,
        amount: Decimal,
        currency: str,
        consumer_email: str,
        merchant_reference: Optional[str] = None,
        consumer_first_name: Optional[str] = None,
        consumer_last_name: Optional[str] = None,
        consumer_phone: Optional[str] = None,
        billing_address: Optional[Dict] = None,
        shipping_address: Optional[Dict] = None,
        items: Optional[List[Dict]] = None,
        tax_amount: Optional[Decimal] = None,
        shipping_amount: Optional[Decimal] = None,
        mode: str = 'standard'
    ) -> Dict:
        """
        Create a new Afterpay checkout session
        
        Args:
            amount: Total order amount
            currency: Currency code (e.g., 'USD', 'AUD')
            consumer_email: Customer email address
            merchant_reference: Your internal order reference
            consumer_first_name: Customer first name
            consumer_last_name: Customer last name
            consumer_phone: Customer phone number
            billing_address: Billing address dictionary
            shipping_address: Shipping address dictionary
            items: List of order items
            tax_amount: Tax amount
            shipping_amount: Shipping amount
            mode: 'standard' or 'express'
        
        Returns:
            Dict containing token, expires, and redirectCheckoutUrl
        """
        logger.info(f"Creating Afterpay checkout: {amount} {currency}")
        
        payload = {
            'amount': {
                'amount': f"{amount:.2f}",
                'currency': currency.upper()
            },
            'consumer': {
                'email': consumer_email
            }
        }
        
        # Add optional consumer fields
        if consumer_first_name:
            payload['consumer']['givenNames'] = consumer_first_name
        if consumer_last_name:
            payload['consumer']['surname'] = consumer_last_name
        if consumer_phone:
            payload['consumer']['phoneNumber'] = consumer_phone
        
        # Add merchant reference
        if merchant_reference:
            payload['merchantReference'] = merchant_reference
        
        # Add billing address
        if billing_address:
            payload['billing'] = billing_address
        
        # Add shipping address
        if shipping_address:
            payload['shipping'] = shipping_address
        
        # Add items
        if items:
            payload['items'] = items
        
        # Add tax amount
        if tax_amount:
            payload['taxAmount'] = {
                'amount': f"{tax_amount:.2f}",
                'currency': currency.upper()
            }
        
        # Add shipping amount
        if shipping_amount:
            payload['shippingAmount'] = {
                'amount': f"{shipping_amount:.2f}",
                'currency': currency.upper()
            }
        
        # Set mode
        if mode == 'express':
            payload['mode'] = 'express'
        
        return self._make_request('POST', '/v2/checkouts', data=payload)
    
    # ====================================================================================
    # PAYMENT ENDPOINTS
    # ====================================================================================
    
    def auth_payment(
        self,
        token: str,
        merchant_reference: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> Dict:
        """
        Authorize a payment (Deferred Payment Flow)
        Authorization expires after 13 days
        
        Args:
            token: Token from checkout creation
            merchant_reference: Update merchant reference
            request_id: UUID for idempotent retries
        
        Returns:
            Payment object with status and details
        """
        logger.info(f"Authorizing Afterpay payment: {token}")
        
        payload = {
            'token': token
        }
        
        if merchant_reference:
            payload['merchantReference'] = merchant_reference
        
        if request_id:
            payload['requestid'] = request_id
        
        # Auth endpoint requires 70s read timeout
        return self._make_request('POST', '/v2/payments/auth', data=payload, timeout_read=70)
    
    def capture_payment_full(
        self,
        token: str,
        merchant_reference: Optional[str] = None
    ) -> Dict:
        """
        Capture full payment immediately (Immediate Payment Flow)
        
        Args:
            token: Token from checkout creation
            merchant_reference: Update merchant reference
        
        Returns:
            Payment object with status and details
        """
        logger.info(f"Capturing full Afterpay payment: {token}")
        
        payload = {
            'token': token
        }
        
        if merchant_reference:
            payload['merchantReference'] = merchant_reference
        
        # Capture endpoint requires 70s read timeout
        return self._make_request('POST', '/v2/payments/capture', data=payload, timeout_read=70)
    
    def capture_payment_partial(
        self,
        order_id: str,
        amount: Optional[Decimal] = None,
        merchant_reference: Optional[str] = None,
        request_id: Optional[str] = None,
        payment_event_reference: Optional[str] = None
    ) -> Dict:
        """
        Capture partial payment after authorization
        
        Args:
            order_id: Afterpay order ID (from auth response)
            amount: Amount to capture (optional, captures remaining if omitted)
            merchant_reference: Update merchant reference
            request_id: UUID for idempotent retries
            payment_event_reference: Unique reference for this capture event
        
        Returns:
            Updated payment object
        """
        logger.info(f"Capturing partial Afterpay payment: {order_id}")
        
        payload = {}
        
        if amount:
            payload['amount'] = {
                'amount': f"{amount:.2f}",
                'currency': 'USD'  # You might want to make this configurable
            }
        
        if merchant_reference:
            payload['merchantReference'] = merchant_reference
        
        if request_id:
            payload['requestId'] = request_id
        
        if payment_event_reference:
            payload['paymentEventMerchantReference'] = payment_event_reference
        
        endpoint = f'/v2/payments/{order_id}/capture'
        return self._make_request('POST', endpoint, data=payload, timeout_read=70)
    
    # ====================================================================================
    # REFUND ENDPOINTS
    # ====================================================================================
    
    def create_refund(
        self,
        order_id: str,
        amount: Decimal,
        currency: str,
        merchant_reference: str,
        request_id: Optional[str] = None,
        refund_merchant_reference: Optional[str] = None
    ) -> Dict:
        """
        Create a full or partial refund
        
        Args:
            order_id: Afterpay order ID
            amount: Refund amount
            currency: Currency code
            merchant_reference: Merchant's refund ID/reference
            request_id: UUID for idempotent retries
            refund_merchant_reference: Unique reference for this refund
        
        Returns:
            Refund object with refundId and details
        """
        logger.info(f"Creating Afterpay refund: {order_id} - ${amount}")
        
        payload = {
            'amount': {
                'amount': f"{amount:.2f}",
                'currency': currency.upper()
            },
            'merchantReference': merchant_reference
        }
        
        if request_id:
            payload['requestId'] = request_id
        
        if refund_merchant_reference:
            payload['refundMerchantReference'] = refund_merchant_reference
        
        endpoint = f'/v2/payments/{order_id}/refund'
        return self._make_request('POST', endpoint, data=payload, timeout_read=70)
    
    # ====================================================================================
    # ORDER MANAGEMENT
    # ====================================================================================
    
    def get_payment_by_token(self, token: str) -> Dict:
        """
        Get payment details by checkout token
        
        Args:
            token: Checkout token
        
        Returns:
            Payment object with order details
        """
        logger.info(f"Fetching Afterpay payment by token: {token}")
        endpoint = f'/v2/payments/{token}'
        return self._make_request('GET', endpoint)
    
    def get_payment_by_order_id(self, order_id: str) -> Dict:
        """
        Get payment details by order ID
        
        Args:
            order_id: Afterpay order ID
        
        Returns:
            Payment object with order details
        """
        logger.info(f"Fetching Afterpay payment by order ID: {order_id}")
        endpoint = f'/v2/payments/{order_id}'
        return self._make_request('GET', endpoint)
    
    def void_payment(self, order_id: str) -> Dict:
        """
        Void an authorized payment
        
        Args:
            order_id: Afterpay order ID
        
        Returns:
            Updated payment object
        """
        logger.info(f"Voiding Afterpay payment: {order_id}")
        endpoint = f'/v2/payments/{order_id}/void'
        return self._make_request('POST', endpoint, data={})
    
    # ====================================================================================
    # HELPER METHODS
    # ====================================================================================
    
    def validate_amount(self, amount: Decimal, currency: str) -> Dict:
        """
        Check if amount is within merchant's payment limits
        
        Args:
            amount: Amount to validate
            currency: Currency code
        
        Returns:
            Dict with 'valid' boolean and 'message' string
        """
        try:
            config = self.get_configuration()
            
            min_amount = Decimal(config.get('minimumAmount', {}).get('amount', '0'))
            max_amount = Decimal(config.get('maximumAmount', {}).get('amount', '0'))
            
            if amount < min_amount:
                return {
                    'valid': False,
                    'message': f'Amount ${amount} is below minimum ${min_amount}'
                }
            
            if amount > max_amount:
                return {
                    'valid': False,
                    'message': f'Amount ${amount} exceeds maximum ${max_amount}'
                }
            
            return {
                'valid': True,
                'message': 'Amount is valid',
                'min_amount': float(min_amount),
                'max_amount': float(max_amount)
            }
        
        except Exception as e:
            logger.error(f"Error validating amount: {e}")
            return {
                'valid': False,
                'message': f'Error validating amount: {str(e)}'
            }
    
    def format_address(
        self,
        name: str,
        line1: str,
        city: str,
        state: str,
        postcode: str,
        country_code: str,
        line2: Optional[str] = None,
        phone: Optional[str] = None
    ) -> Dict:
        """
        Format address for Afterpay API
        
        Returns:
            Properly formatted address dictionary
        """
        address = {
            'name': name,
            'line1': line1,
            'area1': city,
            'region': state,
            'postcode': postcode,
            'countryCode': country_code.upper()
        }
        
        if line2:
            address['line2'] = line2
        
        if phone:
            address['phoneNumber'] = phone
        
        return address
    
    def format_item(
        self,
        name: str,
        quantity: int,
        price: Decimal,
        currency: str,
        sku: Optional[str] = None,
        page_url: Optional[str] = None,
        image_url: Optional[str] = None,
        categories: Optional[List[List[str]]] = None
    ) -> Dict:
        """
        Format order item for Afterpay API
        
        Returns:
            Properly formatted item dictionary
        """
        item = {
            'name': name,
            'quantity': quantity,
            'price': {
                'amount': f"{price:.2f}",
                'currency': currency.upper()
            }
        }
        
        if sku:
            item['sku'] = sku
        
        if page_url:
            item['pageUrl'] = page_url
        
        if image_url:
            item['imageUrl'] = image_url
        
        if categories:
            item['categories'] = categories
        
        return item
