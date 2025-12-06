"""
Custom admin configuration to rename Django apps in the admin interface
"""
from django.contrib import admin
from django.apps import apps

# Get the auth app config and override its verbose name
auth_app = apps.get_app_config('auth')
auth_app.verbose_name = 'Authorization'
