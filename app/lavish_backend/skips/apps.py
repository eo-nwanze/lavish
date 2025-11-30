"""
Skips App Configuration
"""

from django.apps import AppConfig


class SkipsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'skips'
    verbose_name = 'Subscription Skips'
