"""
Shopify Currency and Locale Service
Handles multi-currency support and locale detection
"""

import requests
import logging
from decimal import Decimal
from typing import Dict, Optional
from django.conf import settings
from django.core.cache import cache
from django.utils import translation

logger = logging.getLogger(__name__)


class ShopifyCurrencyService:
    """
    Handle currency conversion and locale-aware formatting
    """
    
    # Supported currencies with symbols
    SUPPORTED_CURRENCIES = {
        'USD': {'name': 'US Dollar', 'symbol': '$', 'decimal_places': 2},
        'EUR': {'name': 'Euro', 'symbol': '€', 'decimal_places': 2},
        'GBP': {'name': 'British Pound', 'symbol': '£', 'decimal_places': 2},
        'CAD': {'name': 'Canadian Dollar', 'symbol': 'C$', 'decimal_places': 2},
        'AUD': {'name': 'Australian Dollar', 'symbol': 'A$', 'decimal_places': 2},
        'JPY': {'name': 'Japanese Yen', 'symbol': '¥', 'decimal_places': 0},
        'CNY': {'name': 'Chinese Yuan', 'symbol': '¥', 'decimal_places': 2},
        'CHF': {'name': 'Swiss Franc', 'symbol': 'CHF', 'decimal_places': 2},
        'SEK': {'name': 'Swedish Krona', 'symbol': 'kr', 'decimal_places': 2},
        'NZD': {'name': 'New Zealand Dollar', 'symbol': 'NZ$', 'decimal_places': 2},
    }
    
    def __init__(self, shop_domain: str, access_token: str):
        self.shop_domain = shop_domain
        self.access_token = access_token
        self.graphql_url = f"https://{shop_domain}/admin/api/2024-10/graphql.json"
    
    def get_shop_currencies(self) -> Dict:
        """
        Fetch shop's enabled currencies from Shopify
        
        Returns:
            Dict with shop currency info and available currencies
        """
        try:
            query = """
            query GetShopCurrencies {
              shop {
                currencyCode
                currencySettings {
                  baseCurrency {
                    currencyCode
                    currencyName
                  }
                }
                enabledPresentmentCurrencies
              }
            }
            """
            
            response = self._make_graphql_request(query)
            
            if response and 'data' in response:
                shop_data = response['data']['shop']
                return {
                    'base_currency': shop_data['currencyCode'],
                    'enabled_currencies': shop_data.get('enabledPresentmentCurrencies', [shop_data['currencyCode']]),
                    'currency_name': self.SUPPORTED_CURRENCIES.get(
                        shop_data['currencyCode'], 
                        {}
                    ).get('name', shop_data['currencyCode'])
                }
            
            # Fallback
            return {
                'base_currency': 'USD',
                'enabled_currencies': ['USD'],
                'currency_name': 'US Dollar'
            }
            
        except Exception as e:
            logger.error(f"Error fetching shop currencies: {str(e)}")
            return {
                'base_currency': 'USD',
                'enabled_currencies': ['USD'],
                'currency_name': 'US Dollar'
            }
    
    def get_localization_info(self, country_code: Optional[str] = None, language_code: Optional[str] = None) -> Dict:
        """
        Get localization information from Shopify
        
        Args:
            country_code: ISO 3166-1 alpha-2 country code (e.g., 'US', 'GB')
            language_code: ISO 639-1 language code (e.g., 'en', 'fr')
            
        Returns:
            Dict with localization details including currency, country, language
        """
        try:
            query = """
            query GetLocalization($country: CountryCode, $language: LanguageCode) {
              localization(country: $country, language: $language) {
                country {
                  name
                  currency {
                    isoCode
                    name
                    symbol
                  }
                }
                language {
                  isoCode
                  name
                  endonymName
                }
                availableCountries {
                  name
                  isoCode
                  currency {
                    isoCode
                    symbol
                  }
                }
                availableLanguages {
                  isoCode
                  name
                  endonymName
                }
              }
            }
            """
            
            variables = {}
            if country_code:
                variables['country'] = country_code
            if language_code:
                variables['language'] = language_code
            
            response = self._make_graphql_request(query, variables)
            
            if response and 'data' in response:
                return response['data']['localization']
            
            return self._get_default_localization()
            
        except Exception as e:
            logger.error(f"Error fetching localization info: {str(e)}")
            return self._get_default_localization()
    
    def convert_currency(self, amount: Decimal, from_currency: str, to_currency: str) -> Decimal:
        """
        Convert amount from one currency to another
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Converted amount
        """
        if from_currency == to_currency:
            return amount
        
        try:
            # Get exchange rate
            rate = self._get_exchange_rate(from_currency, to_currency)
            
            # Convert
            converted = amount * rate
            
            # Round to appropriate decimal places
            decimal_places = self.SUPPORTED_CURRENCIES.get(
                to_currency, {'decimal_places': 2}
            )['decimal_places']
            
            return round(converted, decimal_places)
            
        except Exception as e:
            logger.error(f"Currency conversion error: {str(e)}")
            return amount
    
    def format_price(self, amount: Decimal, currency_code: str, locale: str = 'en_US') -> str:
        """
        Format price according to currency and locale
        
        Args:
            amount: Price amount
            currency_code: Currency code (e.g., 'USD')
            locale: Locale string (e.g., 'en_US', 'fr_FR')
            
        Returns:
            Formatted price string
        """
        try:
            currency_info = self.SUPPORTED_CURRENCIES.get(currency_code)
            
            if not currency_info:
                return f"{currency_code} {amount:.2f}"
            
            symbol = currency_info['symbol']
            decimal_places = currency_info['decimal_places']
            
            # Format based on locale conventions
            if locale.startswith('en'):
                # English: $10.00
                return f"{symbol}{amount:.{decimal_places}f}"
            elif locale.startswith('fr') or locale.startswith('de'):
                # French/German: 10,00 €
                formatted = f"{amount:.{decimal_places}f}".replace('.', ',')
                return f"{formatted} {symbol}"
            else:
                # Default format
                return f"{symbol}{amount:.{decimal_places}f}"
                
        except Exception as e:
            logger.error(f"Price formatting error: {str(e)}")
            return f"{currency_code} {amount:.2f}"
    
    def _get_exchange_rate(self, from_currency: str, to_currency: str) -> Decimal:
        """
        Get exchange rate with caching
        Cache for 1 hour
        """
        cache_key = f'exchange_rate_{from_currency}_{to_currency}'
        cached_rate = cache.get(cache_key)
        
        if cached_rate:
            return Decimal(str(cached_rate))
        
        try:
            # Try external exchange rate API
            api_key = getattr(settings, 'EXCHANGE_RATE_API_KEY', None)
            
            if api_key:
                response = requests.get(
                    f'https://v6.exchangerate-api.com/v6/{api_key}/pair/{from_currency}/{to_currency}',
                    timeout=3
                )
                
                if response.status_code == 200:
                    rate = Decimal(str(response.json()['conversion_rate']))
                    cache.set(cache_key, float(rate), 3600)  # Cache 1 hour
                    return rate
        
        except Exception as e:
            logger.warning(f"Could not fetch live exchange rate: {str(e)}")
        
        # Fallback to approximate rates
        return self._get_approximate_rate(from_currency, to_currency)
    
    def _get_approximate_rate(self, from_currency: str, to_currency: str) -> Decimal:
        """Fallback approximate exchange rates"""
        rates = {
            ('USD', 'EUR'): Decimal('0.85'),
            ('USD', 'GBP'): Decimal('0.73'),
            ('USD', 'CAD'): Decimal('1.25'),
            ('USD', 'AUD'): Decimal('1.35'),
            ('USD', 'JPY'): Decimal('110.0'),
            ('USD', 'CNY'): Decimal('6.45'),
            ('USD', 'CHF'): Decimal('0.92'),
            ('USD', 'SEK'): Decimal('9.0'),
            ('USD', 'NZD'): Decimal('1.42'),
            
            # Reverse rates
            ('EUR', 'USD'): Decimal('1.18'),
            ('GBP', 'USD'): Decimal('1.37'),
            ('CAD', 'USD'): Decimal('0.80'),
            ('AUD', 'USD'): Decimal('0.74'),
            ('JPY', 'USD'): Decimal('0.0091'),
            ('CNY', 'USD'): Decimal('0.155'),
            ('CHF', 'USD'): Decimal('1.09'),
            ('SEK', 'USD'): Decimal('0.11'),
            ('NZD', 'USD'): Decimal('0.70'),
        }
        
        return rates.get((from_currency, to_currency), Decimal('1.0'))
    
    def _make_graphql_request(self, query: str, variables: Optional[Dict] = None) -> Optional[Dict]:
        """Make GraphQL API request to Shopify"""
        try:
            headers = {
                'X-Shopify-Access-Token': self.access_token,
                'Content-Type': 'application/json'
            }
            
            payload = {'query': query}
            if variables:
                payload['variables'] = variables
            
            response = requests.post(
                self.graphql_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            
            logger.error(f"GraphQL request failed: {response.status_code}")
            return None
            
        except Exception as e:
            logger.error(f"GraphQL request error: {str(e)}")
            return None
    
    def _get_default_localization(self) -> Dict:
        """Default localization fallback"""
        return {
            'country': {
                'name': 'United States',
                'currency': {
                    'isoCode': 'USD',
                    'name': 'US Dollar',
                    'symbol': '$'
                }
            },
            'language': {
                'isoCode': 'EN',
                'name': 'English',
                'endonymName': 'English'
            },
            'availableCountries': [],
            'availableLanguages': []
        }


class LocaleMiddleware:
    """
    Django middleware to detect and set user locale and currency
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Detect locale and currency
        self.process_request(request)
        response = self.get_response(request)
        return response
    
    def process_request(self, request):
        """Detect and set locale/currency for request"""
        # Priority: URL param > Session > GeoIP > Accept-Language header > Default
        
        # 1. Language detection
        language = self._detect_language(request)
        translation.activate(language)
        request.LANGUAGE_CODE = language
        
        # 2. Currency detection
        currency = self._detect_currency(request)
        request.currency = currency
        request.session['currency'] = currency
        
        # 3. Country detection
        country = self._detect_country(request)
        request.country = country
        request.session['country'] = country
    
    def _detect_language(self, request) -> str:
        """Detect user's preferred language"""
        # Check URL parameter
        if 'lang' in request.GET:
            return request.GET['lang'].lower()
        
        # Check session
        if 'language' in request.session:
            return request.session['language']
        
        # Check Accept-Language header
        if 'HTTP_ACCEPT_LANGUAGE' in request.META:
            accept_lang = request.META['HTTP_ACCEPT_LANGUAGE']
            return accept_lang.split(',')[0].split('-')[0].lower()
        
        # Default
        return getattr(settings, 'LANGUAGE_CODE', 'en')
    
    def _detect_currency(self, request) -> str:
        """Detect user's preferred currency"""
        # Check URL parameter
        if 'currency' in request.GET:
            return request.GET['currency'].upper()
        
        # Check session
        if 'currency' in request.session:
            return request.session['currency']
        
        # Check GeoIP or country detection
        country = self._detect_country(request)
        return self._country_to_currency(country)
    
    def _detect_country(self, request) -> str:
        """Detect user's country"""
        # Check URL parameter
        if 'country' in request.GET:
            return request.GET['country'].upper()
        
        # Check session
        if 'country' in request.session:
            return request.session['country']
        
        # Try GeoIP (if configured)
        try:
            from django.contrib.gis.geoip2 import GeoIP2
            g = GeoIP2()
            ip = self._get_client_ip(request)
            country = g.country_code(ip)
            if country:
                return country
        except:
            pass
        
        # Default
        return 'US'
    
    def _country_to_currency(self, country_code: str) -> str:
        """Map country code to currency"""
        mapping = {
            'US': 'USD', 'CA': 'CAD', 'GB': 'GBP', 'AU': 'AUD',
            'NZ': 'NZD', 'JP': 'JPY', 'CN': 'CNY', 'CH': 'CHF',
            'SE': 'SEK', 'NO': 'NOK', 'DK': 'DKK',
            # EU countries
            'DE': 'EUR', 'FR': 'EUR', 'IT': 'EUR', 'ES': 'EUR',
            'NL': 'EUR', 'BE': 'EUR', 'AT': 'EUR', 'IE': 'EUR',
            'PT': 'EUR', 'FI': 'EUR', 'GR': 'EUR',
        }
        return mapping.get(country_code, 'USD')
    
    def _get_client_ip(self, request) -> str:
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
