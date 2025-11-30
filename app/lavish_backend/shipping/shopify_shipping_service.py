"""
Shopify Shipping Rate Calculator Service
Handles live shipping rate calculations with currency and locale support
"""

import requests
import logging
from decimal import Decimal
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ShopifyShippingRateCalculator:
    """
    Calculate shipping rates for Shopify orders
    Supports multi-currency and fallback to static rates
    """
    
    # Fallback static rates per country (in USD, will be converted)
    STATIC_RATES = {
        'US': {'standard': 5.99, 'express': 15.99, 'overnight': 29.99},
        'CA': {'standard': 8.99, 'express': 18.99, 'overnight': 34.99},
        'GB': {'standard': 9.99, 'express': 19.99, 'overnight': 39.99},
        'AU': {'standard': 12.99, 'express': 22.99, 'overnight': 44.99},
        'EU': {'standard': 10.99, 'express': 20.99, 'overnight': 40.99},
        'DEFAULT': {'standard': 15.00, 'express': 30.00, 'overnight': 50.00},
    }
    
    def __init__(self, shop_domain: Optional[str] = None, access_token: Optional[str] = None):
        self.shop_domain = shop_domain or getattr(settings, 'SHOPIFY_SHOP_DOMAIN', '7fa66c-ac.myshopify.com')
        self.access_token = access_token or getattr(settings, 'SHOPIFY_ACCESS_TOKEN', '')
        self.base_url = f"https://{self.shop_domain}/admin/api/2024-10"
        
    def calculate_rates(self, rate_request: Dict) -> List[Dict]:
        """
        Calculate shipping rates for a given request
        
        Args:
            rate_request: Shopify rate request data containing origin, destination, items
            
        Returns:
            List of shipping rate options with prices and delivery dates
        """
        try:
            # Try to get live rates from Shopify/Sendal
            live_rates = self._get_live_rates(rate_request)
            
            if live_rates:
                logger.info(f"Retrieved {len(live_rates)} live shipping rates")
                return live_rates
            
            # Fallback to static rates
            logger.warning("Live rates unavailable, using static fallback rates")
            return self._get_static_rates(rate_request)
            
        except Exception as e:
            logger.error(f"Error calculating shipping rates: {str(e)}")
            # Return safe fallback rates
            return self._get_static_rates(rate_request)
    
    def _get_live_rates(self, rate_request: Dict) -> Optional[List[Dict]]:
        """
        Fetch live shipping rates from Shopify/Sendal API
        Includes duties and taxes
        """
        try:
            destination = rate_request['rate']['destination']
            origin = rate_request['rate']['origin']
            items = rate_request['rate']['items']
            currency = rate_request['rate'].get('currency', 'USD')
            
            # Calculate total weight
            total_weight_grams = sum(
                item['grams'] * item['quantity'] 
                for item in items
            )
            
            # Calculate total value
            total_value = sum(
                Decimal(str(item['price'])) * item['quantity'] / 100
                for item in items
            )
            
            # Build cache key
            cache_key = self._build_cache_key(
                origin, destination, total_weight_grams, total_value, currency
            )
            
            # Check cache (15 minute expiry as per Shopify docs)
            cached_rates = cache.get(cache_key)
            if cached_rates:
                logger.info("Returning cached shipping rates")
                return cached_rates
            
            # Make API call to Shopify carrier service
            # This would call your Sendal/shipping plugin endpoint
            rates = self._fetch_carrier_service_rates(
                origin, destination, items, currency, total_weight_grams, total_value
            )
            
            if rates:
                # Cache for 15 minutes
                cache.set(cache_key, rates, 900)
                return rates
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching live rates: {str(e)}")
            return None
    
    def _fetch_carrier_service_rates(
        self,
        origin: Dict,
        destination: Dict,
        items: List[Dict],
        currency: str,
        total_weight_grams: int,
        total_value: Decimal
    ) -> Optional[List[Dict]]:
        """
        Call carrier service API for live rates
        This would integrate with Sendal or other shipping providers
        """
        try:
            # Example: Call Sendal API or Shopify shipping app
            # For now, return None to trigger fallback
            # In production, implement actual API call
            
            # Placeholder for Sendal/shipping app integration
            sendal_endpoint = getattr(settings, 'SENDAL_API_ENDPOINT', None)
            
            if not sendal_endpoint:
                return None
            
            payload = {
                'origin': origin,
                'destination': destination,
                'parcels': [{
                    'weight': total_weight_grams,
                    'weight_unit': 'g',
                    'length': 30,
                    'width': 20,
                    'height': 10,
                    'distance_unit': 'cm'
                }],
                'declared_value': float(total_value),
                'currency': currency,
                'include_duties': True,
                'include_taxes': True
            }
            
            response = requests.post(
                sendal_endpoint,
                json=payload,
                headers={'Authorization': f'Bearer {getattr(settings, "SENDAL_API_KEY", "")}'},
                timeout=8  # 8 second timeout (within Shopify limits)
            )
            
            if response.status_code == 200:
                return self._parse_sendal_response(response.json(), currency)
            
            return None
            
        except requests.Timeout:
            logger.warning("Carrier service request timed out")
            return None
        except Exception as e:
            logger.error(f"Carrier service error: {str(e)}")
            return None
    
    def _parse_sendal_response(self, data: Dict, currency: str) -> List[Dict]:
        """Parse Sendal/carrier service response into Shopify ShippingRate format"""
        rates = []
        
        for rate in data.get('rates', []):
            price_amount = Decimal(str(rate['total_price']))
            rates.append({
                'handle': rate['code'],  # Human-readable unique identifier
                'title': rate['name'],   # Name of the shipping rate
                'price': {
                    'amount': str(price_amount),
                    'currencyCode': currency
                },
                'description': rate.get('description', ''),
                'min_delivery_date': rate.get('min_delivery_date'),
                'max_delivery_date': rate.get('max_delivery_date'),
                'phone_required': rate.get('phone_required', False)
            })
        
        return rates
    
    def _get_static_rates(self, rate_request: Dict) -> List[Dict]:
        """
        Generate static fallback rates based on destination country
        """
        destination = rate_request['rate']['destination']
        currency = rate_request['rate'].get('currency', 'USD')
        country_code = destination.get('country', 'US')
        
        # Determine rate table (use EU rates for EU countries)
        eu_countries = ['DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'AT', 'IE', 'PT', 'FI', 'SE']
        rate_key = 'EU' if country_code in eu_countries else country_code
        rates_usd = self.STATIC_RATES.get(rate_key, self.STATIC_RATES['DEFAULT'])
        
        # Convert rates to target currency
        rates_converted = self._convert_rates_to_currency(rates_usd, currency)
        
        # Build response using Shopify ShippingRate object structure
        today = datetime.now()
        
        return [
            {
                'handle': 'standard-shipping',
                'title': 'Standard Shipping',
                'price': {
                    'amount': str(rates_converted['standard']),
                    'currencyCode': currency
                },
                'description': '5-7 business days',
                'min_delivery_date': (today + timedelta(days=5)).isoformat(),
                'max_delivery_date': (today + timedelta(days=7)).isoformat(),
            },
            {
                'handle': 'express-shipping',
                'title': 'Express Shipping',
                'price': {
                    'amount': str(rates_converted['express']),
                    'currencyCode': currency
                },
                'description': '2-3 business days',
                'min_delivery_date': (today + timedelta(days=2)).isoformat(),
                'max_delivery_date': (today + timedelta(days=3)).isoformat(),
            },
            {
                'handle': 'overnight-shipping',
                'title': 'Overnight Shipping',
                'price': {
                    'amount': str(rates_converted['overnight']),
                    'currencyCode': currency
                },
                'description': 'Next business day',
                'min_delivery_date': (today + timedelta(days=1)).isoformat(),
                'max_delivery_date': (today + timedelta(days=1)).isoformat(),
                'phone_required': True
            }
        ]
    
    def _convert_rates_to_currency(self, rates_usd: Dict, target_currency: str) -> Dict:
        """Convert USD rates to target currency using exchange rates"""
        if target_currency == 'USD':
            return rates_usd
        
        # Get exchange rate from settings or API
        exchange_rate = self._get_exchange_rate('USD', target_currency)
        
        return {
            key: Decimal(str(value)) * exchange_rate
            for key, value in rates_usd.items()
        }
    
    def _get_exchange_rate(self, from_currency: str, to_currency: str) -> Decimal:
        """
        Get exchange rate from cache or external API
        Fallback to approximate rates if API unavailable
        """
        cache_key = f'exchange_rate_{from_currency}_{to_currency}'
        cached_rate = cache.get(cache_key)
        
        if cached_rate:
            return Decimal(str(cached_rate))
        
        try:
            # Try to fetch from exchange rate API
            # Example: Using exchangerate-api.com or similar
            api_key = getattr(settings, 'EXCHANGE_RATE_API_KEY', None)
            
            if api_key:
                response = requests.get(
                    f'https://v6.exchangerate-api.com/v6/{api_key}/pair/{from_currency}/{to_currency}',
                    timeout=3
                )
                
                if response.status_code == 200:
                    rate = Decimal(str(response.json()['conversion_rate']))
                    # Cache for 1 hour
                    cache.set(cache_key, float(rate), 3600)
                    return rate
        
        except Exception as e:
            logger.warning(f"Could not fetch exchange rate: {str(e)}")
        
        # Fallback approximate rates
        approximate_rates = {
            ('USD', 'EUR'): Decimal('0.85'),
            ('USD', 'GBP'): Decimal('0.73'),
            ('USD', 'CAD'): Decimal('1.25'),
            ('USD', 'AUD'): Decimal('1.35'),
            ('USD', 'JPY'): Decimal('110.0'),
            ('USD', 'CNY'): Decimal('6.45'),
        }
        
        return approximate_rates.get((from_currency, to_currency), Decimal('1.0'))
    
    def _build_cache_key(
        self,
        origin: Dict,
        destination: Dict,
        weight: int,
        value: Decimal,
        currency: str
    ) -> str:
        """Build cache key for rate lookup"""
        return (
            f"shipping_rate_"
            f"{origin['postal_code']}_{destination['postal_code']}_"
            f"{weight}_{int(value)}_{currency}"
        )


class ShopifyCarrierServiceWebhook:
    """
    Handle Shopify carrier service webhook requests
    This is the callback endpoint that Shopify calls during checkout
    """
    
    @staticmethod
    def handle_rate_request(request_data: Dict) -> Dict:
        """
        Process incoming rate request from Shopify
        
        Args:
            request_data: Shopify rate request payload
            
        Returns:
            Dict with 'rates' key containing list of available shipping options
        """
        try:
            # Extract shop domain from request or use default
            shop_domain = request_data.get('shop_domain', settings.SHOPIFY_SHOP_DOMAIN)
            access_token = settings.SHOPIFY_ACCESS_TOKEN
            
            # Initialize calculator
            calculator = ShopifyShippingRateCalculator(shop_domain, access_token)
            
            # Calculate rates
            rates = calculator.calculate_rates(request_data)
            
            return {'rates': rates}
            
        except Exception as e:
            logger.error(f"Error handling rate request: {str(e)}")
            # Return empty rates to trigger Shopify's backup rates
            return {'rates': []}
