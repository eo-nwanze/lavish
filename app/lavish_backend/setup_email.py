#!/usr/bin/env python
"""
Script to create email configuration
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from email_manager.models import EmailConfiguration

print("🔧 Setting up email configuration...")

# Remove default from existing configs
EmailConfiguration.objects.filter(is_default=True).update(is_default=False)

# Create new configuration
config = EmailConfiguration.objects.create(
    name='Lavish Library Email',
    email_host='server109.web-hosting.com',
    email_port=587,
    email_host_user='auth@endevops.com',
    email_host_password='press30+Five@2025',
    email_use_tls=True,
    email_use_ssl=False,
    default_from_email='auth@endevops.com',
    is_default=True,
)

print(f"✅ Created email configuration: {config.name}")
print(f"   Host: {config.email_host}:{config.email_port}")
print(f"   From: {config.default_from_email}")
print(f"   TLS: {config.email_use_tls}")
print("\n✅ Email configuration ready!")
