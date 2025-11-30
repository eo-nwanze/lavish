"""
Context processors for currency and locale
Makes currency info available in all templates
"""

from django.conf import settings
from .models import Country


def currency_context(request):
    """
    Add currency and locale information to template context
    
    Usage in templates:
        {{ current_currency }} - Current currency code (USD, EUR, etc.)
        {{ currency_symbol }} - Currency symbol ($, €, £, etc.)
        {{ supported_currencies }} - List of available currencies
        {{ current_country }} - Current country code
        {{ current_language }} - Current language code
    """
    currency = getattr(request, 'currency', 'USD')
    country = getattr(request, 'country', 'US')
    language = getattr(request, 'LANGUAGE_CODE', 'en')
    
    # Get currency symbol from Country model
    currency_symbol = '$'
    try:
        country_obj = Country.objects.filter(currency=currency).first()
        if country_obj:
            currency_symbol = country_obj.currency_symbol
    except:
        pass
    
    # Supported currencies from settings
    supported = getattr(settings, 'SUPPORTED_CURRENCIES', ['USD', 'EUR', 'GBP', 'CAD', 'AUD'])
    
    return {
        'current_currency': currency,
        'currency_symbol': currency_symbol,
        'supported_currencies': supported,
        'current_country': country,
        'current_language': language,
    }
