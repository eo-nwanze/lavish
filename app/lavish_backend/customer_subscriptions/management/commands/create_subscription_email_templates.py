"""
Management command to create default email templates for subscription notifications
"""
from django.core.management.base import BaseCommand
from email_manager.models import EmailTemplate, EmailConfiguration
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Create default email templates for subscription notifications'

    def handle(self, *args, **options):
        self.stdout.write('Creating subscription email templates...')
        
        # Get default email configuration
        config = EmailConfiguration.get_default()
        
        templates = [
            {
                'name': 'subscription_skip_notification',
                'template_type': 'custom',
                'subject': '✅ Subscription Delivery Skipped - {{ month_name }}',
                'html_content': self.get_skip_notification_html(),
                'plain_text_content': self.get_skip_notification_plain(),
                'variables': {
                    'customer_name': 'John Doe',
                    'subscription_name': 'Monthly Book Box',
                    'month_name': 'January 2025',
                    'next_delivery_date': '2025-02-15',
                    'skips_remaining': 2,
                    'skip_reset_date': '2025-03-01',
                    'unskip_deadline': '2025-01-10',
                    'dashboard_url': 'https://your-store.myshopify.com/account',
                },
            },
            {
                'name': 'subscription_address_change_notification',
                'template_type': 'custom',
                'subject': '📍 Delivery Address Updated for Your Subscription',
                'html_content': self.get_address_change_html(),
                'plain_text_content': self.get_address_change_plain(),
                'variables': {
                    'customer_name': 'John Doe',
                    'subscription_name': 'Monthly Book Box',
                    'old_address': '123 Old Street, Old City, OS 12345',
                    'new_address': '456 New Avenue, New City, NS 67890',
                    'next_delivery_date': '2025-02-15',
                    'change_date': '2025-01-15',
                    'affected_orders_count': 2,
                    'dashboard_url': 'https://your-store.myshopify.com/account',
                },
            },
            {
                'name': 'subscription_renewal_reminder',
                'template_type': 'custom',
                'subject': '🔔 Your Subscription Renews Soon - {{ subscription_name }}',
                'html_content': self.get_renewal_reminder_html(),
                'plain_text_content': self.get_renewal_reminder_plain(),
                'variables': {
                    'customer_name': 'John Doe',
                    'subscription_name': 'Monthly Book Box',
                    'renewal_date': '2025-02-01',
                    'renewal_cost': '$29.99',
                    'shipping_cost': '$5.00',
                    'total_cost': '$34.99',
                    'payment_method': 'Visa ending in 1234',
                    'delivery_address': '123 Main Street, City, ST 12345',
                    'dashboard_url': 'https://your-store.myshopify.com/account',
                },
            },
            {
                'name': 'subscription_cancellation_confirmation',
                'template_type': 'custom',
                'subject': '😢 Subscription Cancelled - We\'ll Miss You',
                'html_content': self.get_cancellation_confirmation_html(),
                'plain_text_content': self.get_cancellation_confirmation_plain(),
                'variables': {
                    'customer_name': 'John Doe',
                    'subscription_name': 'Monthly Book Box',
                    'cancellation_date': '2025-01-15',
                    'final_delivery_date': '2025-02-01',
                    'feedback_reason': 'Too expensive',
                    'reactivate_url': 'https://your-store.myshopify.com/account',
                },
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for template_data in templates:
            template, created = EmailTemplate.objects.update_or_create(
                name=template_data['name'],
                defaults={
                    'template_type': template_data['template_type'],
                    'subject': template_data['subject'],
                    'html_content': template_data['html_content'],
                    'plain_text_content': template_data['plain_text_content'],
                    'variables': template_data['variables'],
                    'configuration': config,
                    'is_active': True,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✅ Created: {template.name}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'📝 Updated: {template.name}'))
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Complete! Created {created_count}, Updated {updated_count} templates'
            )
        )
    
    def get_skip_notification_html(self):
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Subscription Delivery Skipped</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; background-color: #f5f5f5; }
        .container { background-color: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin: 20px; }
        .header { background: linear-gradient(135deg, #6B46C1 0%, #9333EA 100%); color: white; padding: 30px 20px; text-align: center; }
        .header h1 { margin: 0; font-size: 28px; font-weight: 600; }
        .content { padding: 30px 25px; }
        .info-box { background-color: #F3F4F6; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #9333EA; }
        .info-box h3 { margin-top: 0; color: #6B46C1; font-size: 18px; }
        .info-row { margin: 12px 0; display: flex; justify-content: space-between; align-items: center; }
        .info-label { font-weight: 600; color: #555; }
        .info-value { color: #333; }
        .button { display: inline-block; background-color: #9333EA; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 20px 0; transition: background-color 0.3s; }
        .button:hover { background-color: #7C3AED; }
        .footer { text-align: center; margin-top: 30px; padding: 20px; background-color: #F9FAFB; color: #6B7280; font-size: 13px; border-top: 1px solid #E5E7EB; }
        .alert { background-color: #FEF3C7; border-left: 4px solid #F59E0B; padding: 15px; border-radius: 6px; margin: 20px 0; }
        .alert-text { color: #92400E; margin: 0; }
        .success-badge { background-color: #10B981; color: white; padding: 6px 12px; border-radius: 20px; font-size: 14px; font-weight: 600; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✅ Delivery Skipped</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.95;">Your subscription delivery has been paused</p>
        </div>
        
        <div class="content">
            <p>Hi <strong>{{ customer_name }}</strong>,</p>
            
            <p>This is to confirm that your <strong>{{ subscription_name }}</strong> delivery for <strong>{{ month_name }}</strong> has been successfully skipped.</p>
            
            <div class="info-box">
                <h3>📦 Skip Details</h3>
                <div class="info-row">
                    <span class="info-label">Subscription:</span>
                    <span class="info-value">{{ subscription_name }}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Skipped Month:</span>
                    <span class="info-value">{{ month_name }}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Next Delivery:</span>
                    <span class="info-value">{{ next_delivery_date }}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Skips Remaining:</span>
                    <span class="info-value"><span class="success-badge">{{ skips_remaining }} left</span></span>
                </div>
                <div class="info-row">
                    <span class="info-label">Skips Reset On:</span>
                    <span class="info-value">{{ skip_reset_date }}</span>
                </div>
            </div>
            
            {% if unskip_deadline %}
            <div class="alert">
                <p class="alert-text">
                    <strong>⏰ Changed your mind?</strong><br>
                    You can unskip this delivery until <strong>{{ unskip_deadline }}</strong>.
                    After this deadline, your skip will be confirmed and cannot be reversed.
                </p>
            </div>
            {% endif %}
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{{ dashboard_url }}" class="button">Manage My Subscription</a>
            </div>
            
            <p style="color: #6B7280; font-size: 14px; margin-top: 25px;">
                Your subscription will automatically resume with the next scheduled delivery on {{ next_delivery_date }}.
                You won't be charged for this skipped month.
            </p>
        </div>
        
        <div class="footer">
            <p>Need help? Contact us at support@lavish-library.com</p>
            <p>&copy; 2025 Lavish Library. All rights reserved.</p>
        </div>
    </div>
</body>
</html>"""
    
    def get_skip_notification_plain(self):
        return """Subscription Delivery Skipped

Hi {{ customer_name }},

This is to confirm that your {{ subscription_name }} delivery for {{ month_name }} has been successfully skipped.

Skip Details:
- Subscription: {{ subscription_name }}
- Skipped Month: {{ month_name }}
- Next Delivery: {{ next_delivery_date }}
- Skips Remaining: {{ skips_remaining }} left
- Skips Reset On: {{ skip_reset_date }}

{% if unskip_deadline %}
Changed your mind?
You can unskip this delivery until {{ unskip_deadline }}.
After this deadline, your skip will be confirmed and cannot be reversed.
{% endif %}

Your subscription will automatically resume with the next scheduled delivery on {{ next_delivery_date }}.
You won't be charged for this skipped month.

Manage your subscription: {{ dashboard_url }}

Need help? Contact us at support@lavish-library.com

© 2025 Lavish Library. All rights reserved."""
    
    def get_address_change_html(self):
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Delivery Address Updated</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; background-color: #f5f5f5; }
        .container { background-color: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin: 20px; }
        .header { background: linear-gradient(135deg, #0891B2 0%, #06B6D4 100%); color: white; padding: 30px 20px; text-align: center; }
        .header h1 { margin: 0; font-size: 28px; font-weight: 600; }
        .content { padding: 30px 25px; }
        .address-box { background-color: #F0FDF4; padding: 20px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #10B981; }
        .old-address-box { background-color: #FEF2F2; border-left: 4px solid #EF4444; }
        .address-label { font-weight: 600; color: #065F46; margin-bottom: 8px; display: block; }
        .old-address-label { color: #991B1B; }
        .address-text { color: #374151; line-height: 1.8; }
        .info-box { background-color: #EFF6FF; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #3B82F6; }
        .button { display: inline-block; background-color: #0891B2; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 20px 0; }
        .button:hover { background-color: #0E7490; }
        .footer { text-align: center; margin-top: 30px; padding: 20px; background-color: #F9FAFB; color: #6B7280; font-size: 13px; border-top: 1px solid #E5E7EB; }
        .badge { background-color: #3B82F6; color: white; padding: 6px 12px; border-radius: 20px; font-size: 13px; font-weight: 600; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📍 Address Updated</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.95;">Your delivery address has been changed</p>
        </div>
        
        <div class="content">
            <p>Hi <strong>{{ customer_name }}</strong>,</p>
            
            <p>We're writing to confirm that the delivery address for your <strong>{{ subscription_name }}</strong> has been successfully updated on <strong>{{ change_date }}</strong>.</p>
            
            <div class="address-box old-address-box">
                <span class="address-label old-address-label">❌ Old Address:</span>
                <div class="address-text">{{ old_address }}</div>
            </div>
            
            <div class="address-box">
                <span class="address-label">✅ New Address:</span>
                <div class="address-text">{{ new_address }}</div>
            </div>
            
            <div class="info-box">
                <p style="margin: 0; color: #1E40AF;">
                    <strong>📦 Impact on Your Orders:</strong><br>
                    {% if affected_orders_count > 0 %}
                    This change has been applied to <span class="badge">{{ affected_orders_count }} upcoming order(s)</span> that haven't shipped yet.
                    Your next delivery on <strong>{{ next_delivery_date }}</strong> will be sent to the new address.
                    {% else %}
                    All upcoming deliveries, starting with your next delivery on <strong>{{ next_delivery_date }}</strong>, will be sent to the new address.
                    {% endif %}
                </p>
            </div>
            
            <div style="background-color: #FEF3C7; padding: 15px; border-radius: 6px; margin: 20px 0; border-left: 4px solid #F59E0B;">
                <p style="margin: 0; color: #92400E;">
                    <strong>⚠️ Already Shipped Orders:</strong><br>
                    Orders that have already been shipped will continue to the original address and cannot be redirected.
                </p>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{{ dashboard_url }}" class="button">View My Subscription</a>
            </div>
            
            <p style="color: #6B7280; font-size: 14px; margin-top: 25px;">
                If you didn't make this change or believe this is an error, please contact our support team immediately.
            </p>
        </div>
        
        <div class="footer">
            <p>Need help? Contact us at support@lavish-library.com</p>
            <p>&copy; 2025 Lavish Library. All rights reserved.</p>
        </div>
    </div>
</body>
</html>"""
    
    def get_address_change_plain(self):
        return """Delivery Address Updated

Hi {{ customer_name }},

We're writing to confirm that the delivery address for your {{ subscription_name }} has been successfully updated on {{ change_date }}.

OLD ADDRESS:
{{ old_address }}

NEW ADDRESS:
{{ new_address }}

IMPACT ON YOUR ORDERS:
{% if affected_orders_count > 0 %}
This change has been applied to {{ affected_orders_count }} upcoming order(s) that haven't shipped yet.
{% endif %}
Your next delivery on {{ next_delivery_date }} will be sent to the new address.

IMPORTANT:
Orders that have already been shipped will continue to the original address and cannot be redirected.

If you didn't make this change or believe this is an error, please contact our support team immediately.

View your subscription: {{ dashboard_url }}

Need help? Contact us at support@lavish-library.com

© 2025 Lavish Library. All rights reserved."""
    
    def get_renewal_reminder_html(self):
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Subscription Renewal Reminder</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; background-color: #f5f5f5; }
        .container { background-color: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin: 20px; }
        .header { background: linear-gradient(135deg, #F59E0B 0%, #FBBF24 100%); color: white; padding: 30px 20px; text-align: center; }
        .header h1 { margin: 0; font-size: 28px; font-weight: 600; }
        .content { padding: 30px 25px; }
        .info-box { background-color: #F9FAFB; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .info-row { display: flex; justify-content: space-between; margin: 12px 0; padding-bottom: 12px; border-bottom: 1px solid #E5E7EB; }
        .info-row:last-child { border-bottom: none; }
        .info-label { font-weight: 600; color: #6B7280; }
        .info-value { color: #111827; font-weight: 500; }
        .total-row { background-color: #ECFDF5; padding: 15px; border-radius: 6px; margin-top: 15px; }
        .total-label { font-size: 18px; font-weight: 700; color: #065F46; }
        .total-value { font-size: 24px; font-weight: 700; color: #10B981; }
        .button { display: inline-block; background-color: #F59E0B; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 20px 0; }
        .button:hover { background-color: #D97706; }
        .footer { text-align: center; margin-top: 30px; padding: 20px; background-color: #F9FAFB; color: #6B7280; font-size: 13px; border-top: 1px solid #E5E7EB; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔔 Renewal Reminder</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.95;">Your subscription renews soon</p>
        </div>
        
        <div class="content">
            <p>Hi <strong>{{ customer_name }}</strong>,</p>
            
            <p>Your <strong>{{ subscription_name }}</strong> is scheduled to renew on <strong>{{ renewal_date }}</strong>.</p>
            
            <div class="info-box">
                <h3 style="margin-top: 0; color: #111827;">📋 Renewal Details</h3>
                <div class="info-row">
                    <span class="info-label">Renewal Date:</span>
                    <span class="info-value">{{ renewal_date }}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Subscription Cost:</span>
                    <span class="info-value">{{ renewal_cost }}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Shipping:</span>
                    <span class="info-value">{{ shipping_cost }}</span>
                </div>
                <div class="total-row info-row">
                    <span class="total-label">Total Amount:</span>
                    <span class="total-value">{{ total_cost }}</span>
                </div>
            </div>
            
            <div class="info-box">
                <h3 style="margin-top: 0; color: #111827;">💳 Payment & Delivery</h3>
                <div class="info-row">
                    <span class="info-label">Payment Method:</span>
                    <span class="info-value">{{ payment_method }}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Delivery Address:</span>
                    <span class="info-value">{{ delivery_address }}</span>
                </div>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{{ dashboard_url }}" class="button">Manage Subscription</a>
            </div>
            
            <p style="color: #6B7280; font-size: 14px; margin-top: 25px;">
                No action is required. Your payment method will be charged automatically on the renewal date.
                You can update your payment method, delivery address, or cancel anytime from your account dashboard.
            </p>
        </div>
        
        <div class="footer">
            <p>Need help? Contact us at support@lavish-library.com</p>
            <p>&copy; 2025 Lavish Library. All rights reserved.</p>
        </div>
    </div>
</body>
</html>"""
    
    def get_renewal_reminder_plain(self):
        return """Subscription Renewal Reminder

Hi {{ customer_name }},

Your {{ subscription_name }} is scheduled to renew on {{ renewal_date }}.

RENEWAL DETAILS:
- Renewal Date: {{ renewal_date }}
- Subscription Cost: {{ renewal_cost }}
- Shipping: {{ shipping_cost }}
- Total Amount: {{ total_cost }}

PAYMENT & DELIVERY:
- Payment Method: {{ payment_method }}
- Delivery Address: {{ delivery_address }}

No action is required. Your payment method will be charged automatically on the renewal date.
You can update your payment method, delivery address, or cancel anytime from your account dashboard.

Manage your subscription: {{ dashboard_url }}

Need help? Contact us at support@lavish-library.com

© 2025 Lavish Library. All rights reserved."""
    
    def get_cancellation_confirmation_html(self):
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Subscription Cancelled</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; background-color: #f5f5f5; }
        .container { background-color: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin: 20px; }
        .header { background: linear-gradient(135deg, #6B7280 0%, #9CA3AF 100%); color: white; padding: 30px 20px; text-align: center; }
        .header h1 { margin: 0; font-size: 28px; font-weight: 600; }
        .content { padding: 30px 25px; }
        .info-box { background-color: #F9FAFB; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #6B7280; }
        .button { display: inline-block; background-color: #10B981; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 20px 0; }
        .button:hover { background-color: #059669; }
        .footer { text-align: center; margin-top: 30px; padding: 20px; background-color: #F9FAFB; color: #6B7280; font-size: 13px; border-top: 1px solid #E5E7EB; }
        .highlight-box { background-color: #DBEAFE; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>😢 Subscription Cancelled</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.95;">We're sorry to see you go</p>
        </div>
        
        <div class="content">
            <p>Hi <strong>{{ customer_name }}</strong>,</p>
            
            <p>Your <strong>{{ subscription_name }}</strong> has been cancelled as of <strong>{{ cancellation_date }}</strong>.</p>
            
            <div class="info-box">
                <h3 style="margin-top: 0;">📦 What Happens Next</h3>
                <p style="margin: 10px 0;">
                    <strong>Final Delivery:</strong> {{ final_delivery_date }}<br>
                    You'll receive your last box as scheduled. No further charges will be made after this delivery.
                </p>
                {% if feedback_reason %}
                <p style="margin: 15px 0 0 0; color: #6B7280; font-size: 14px;">
                    <strong>Cancellation Reason:</strong> {{ feedback_reason }}
                </p>
                {% endif %}
            </div>
            
            <div class="highlight-box">
                <h3 style="margin-top: 0; color: #1E40AF;">💙 We'd Love to Have You Back!</h3>
                <p style="margin: 10px 0; color: #1F2937;">
                    Changed your mind? You can reactivate your subscription anytime.
                </p>
                <a href="{{ reactivate_url }}" class="button">Reactivate Subscription</a>
            </div>
            
            <p style="color: #6B7280; font-size: 14px; margin-top: 25px;">
                Thank you for being part of our community! If you have any feedback or questions,
                we'd love to hear from you at support@lavish-library.com
            </p>
        </div>
        
        <div class="footer">
            <p>Questions? Contact us at support@lavish-library.com</p>
            <p>&copy; 2025 Lavish Library. All rights reserved.</p>
        </div>
    </div>
</body>
</html>"""
    
    def get_cancellation_confirmation_plain(self):
        return """Subscription Cancelled

Hi {{ customer_name }},

Your {{ subscription_name }} has been cancelled as of {{ cancellation_date }}.

WHAT HAPPENS NEXT:
Final Delivery: {{ final_delivery_date }}
You'll receive your last box as scheduled. No further charges will be made after this delivery.

{% if feedback_reason %}
Cancellation Reason: {{ feedback_reason }}
{% endif %}

WE'D LOVE TO HAVE YOU BACK!
Changed your mind? You can reactivate your subscription anytime.
Reactivate: {{ reactivate_url }}

Thank you for being part of our community! If you have any feedback or questions,
we'd love to hear from you at support@lavish-library.com

Questions? Contact us at support@lavish-library.com

© 2025 Lavish Library. All rights reserved."""
