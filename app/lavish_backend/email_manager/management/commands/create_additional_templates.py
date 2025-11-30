from django.core.management.base import BaseCommand
from email_manager.models import EmailTemplate, EmailConfiguration


class Command(BaseCommand):
    help = 'Creates additional subscription email templates'

    def handle(self, *args, **options):
        self.stdout.write('Creating additional subscription email templates...')
        
        config = EmailConfiguration.objects.filter(is_default=True).first()
        
        templates_created = 0
        templates_updated = 0
        
        # Template 1: Welcome Email
        template, created = EmailTemplate.objects.update_or_create(
            name='subscription_welcome',
            defaults={
                'template_type': 'welcome',
                'subject': 'Welcome to {{ subscription_name }}!',
                'html_content': '''<!DOCTYPE html>
<html>
<head>
<style>
body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
.container { max-width: 600px; margin: 0 auto; padding: 20px; }
.header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
.header h1 { margin: 0; font-size: 28px; }
.content { background: #fff; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.info-box { background: #f8f9fa; border-left: 4px solid #667eea; padding: 15px; margin: 20px 0; border-radius: 5px; }
.detail-item { margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 5px; }
.detail-label { font-weight: bold; color: #667eea; }
.cta-button { display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; margin: 20px 0; font-weight: bold; }
.footer { text-align: center; margin-top: 30px; color: #666; font-size: 14px; }
</style>
</head>
<body>
<div class="container">
<div class="header">
<h1>Welcome to Lavish Library!</h1>
</div>
<div class="content">
<p>Hi {{ customer_name }},</p>
<p>Welcome to <strong>{{ subscription_name }}</strong>! We are thrilled to have you.</p>
<div class="info-box">
<strong>Your subscription is now active!</strong><br>
First delivery: <strong>{{ first_delivery_date }}</strong>
</div>
<div class="detail-item"><span class="detail-label">Subscription:</span> {{ subscription_name }}</div>
<div class="detail-item"><span class="detail-label">Billing Frequency:</span> {{ billing_frequency }}</div>
<div class="detail-item"><span class="detail-label">Monthly Cost:</span> £{{ monthly_cost }}</div>
<div style="text-align: center;">
<a href="{{ dashboard_url }}" class="cta-button">Go to My Dashboard</a>
</div>
<p>Happy reading!<br><strong>The Lavish Library Team</strong></p>
</div>
<div class="footer">
<p>Lavish Library | support@lavish-library.com</p>
</div>
</div>
</body>
</html>''',
                'plain_text_content': '''Welcome to {{ subscription_name }}!

Hi {{ customer_name }},

Welcome to {{ subscription_name }}! We are thrilled to have you.

YOUR SUBSCRIPTION IS NOW ACTIVE!
First delivery: {{ first_delivery_date }}

Subscription: {{ subscription_name }}
Billing Frequency: {{ billing_frequency }}
Monthly Cost: £{{ monthly_cost }}

Manage your subscription: {{ dashboard_url }}

Happy reading!
The Lavish Library Team''',
                'variables': {
                    'customer_name': 'John',
                    'subscription_name': 'Premium Monthly Box',
                    'first_delivery_date': 'January 15, 2025',
                    'billing_frequency': 'Monthly',
                    'monthly_cost': '37.90',
                    'dashboard_url': 'https://7fa66c-ac.myshopify.com/account',
                },
                'is_active': True,
                'configuration': config
            }
        )
        
        if created:
            templates_created += 1
            self.stdout.write(self.style.SUCCESS(f'Created: {template.name}'))
        else:
            templates_updated += 1
            self.stdout.write(self.style.WARNING(f'Updated: {template.name}'))
        
        # Template 2: Payment Failure
        template, created = EmailTemplate.objects.update_or_create(
            name='subscription_payment_failure',
            defaults={
                'template_type': 'custom',
                'subject': 'Payment Failed - Action Required for {{ subscription_name }}',
                'html_content': '''<!DOCTYPE html>
<html>
<head>
<style>
body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
.container { max-width: 600px; margin: 0 auto; padding: 20px; }
.header { background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
.header h1 { margin: 0; font-size: 28px; }
.content { background: #fff; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.alert-box { background: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin: 20px 0; border-radius: 5px; }
.detail-row { display: flex; justify-content: space-between; margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 5px; }
.cta-button { display: inline-block; background: #dc3545; color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; margin: 20px 0; font-weight: bold; }
.footer { text-align: center; margin-top: 30px; color: #666; font-size: 14px; }
</style>
</head>
<body>
<div class="container">
<div class="header">
<h1>Payment Failed</h1>
</div>
<div class="content">
<p>Hi {{ customer_name }},</p>
<div class="alert-box">
<strong>Action Required:</strong> We were unable to process payment for your {{ subscription_name }} subscription.
</div>
<div class="detail-row"><span><strong>Amount Due:</strong></span><span style="color: #dc3545;">£{{ amount_due }}</span></div>
<div class="detail-row"><span><strong>Billing Date:</strong></span><span>{{ billing_date }}</span></div>
<div class="detail-row"><span><strong>Failure Reason:</strong></span><span>{{ failure_reason }}</span></div>
<p>We will automatically retry in {{ retry_days }} days.</p>
<div style="text-align: center;">
<a href="{{ update_payment_url }}" class="cta-button">Update Payment Method</a>
</div>
</div>
<div class="footer">
<p>Lavish Library | support@lavish-library.com</p>
</div>
</div>
</body>
</html>''',
                'plain_text_content': '''Payment Failed - Action Required

Hi {{ customer_name }},

ACTION REQUIRED: We were unable to process payment for your {{ subscription_name }} subscription.

Amount Due: £{{ amount_due }}
Billing Date: {{ billing_date }}
Failure Reason: {{ failure_reason }}

We will automatically retry in {{ retry_days }} days.

Update payment method: {{ update_payment_url }}

Lavish Library | support@lavish-library.com''',
                'variables': {
                    'customer_name': 'Michael',
                    'subscription_name': 'Premium Monthly Box',
                    'amount_due': '37.90',
                    'billing_date': 'January 1, 2025',
                    'failure_reason': 'Insufficient funds',
                    'retry_days': '3',
                    'update_payment_url': 'https://7fa66c-ac.myshopify.com/account',
                },
                'is_active': True,
                'configuration': config
            }
        )
        
        if created:
            templates_created += 1
            self.stdout.write(self.style.SUCCESS(f'Created: {template.name}'))
        else:
            templates_updated += 1
            self.stdout.write(self.style.WARNING(f'Updated: {template.name}'))
        
        # Template 3: Address Change Reminder
        template, created = EmailTemplate.objects.update_or_create(
            name='subscription_address_reminder',
            defaults={
                'template_type': 'custom',
                'subject': 'Address Change Deadline - {{ subscription_name }}',
                'html_content': '''<!DOCTYPE html>
<html>
<head>
<style>
body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
.container { max-width: 600px; margin: 0 auto; padding: 20px; }
.header { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
.header h1 { margin: 0; font-size: 28px; }
.content { background: #fff; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.alert-box { background: #fff3cd; border-left: 4px solid #ff6b6b; padding: 15px; margin: 20px 0; border-radius: 5px; }
.deadline-box { background: #ff6b6b; color: white; padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0; }
.current-address { background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }
.cta-button { display: inline-block; background: #ff6b6b; color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; margin: 20px 0; font-weight: bold; }
.footer { text-align: center; margin-top: 30px; color: #666; font-size: 14px; }
</style>
</head>
<body>
<div class="container">
<div class="header">
<h1>Address Change Deadline</h1>
</div>
<div class="content">
<p>Hi {{ customer_name }},</p>
<div class="alert-box">
<strong>Important:</strong> Address change deadline for your {{ subscription_name }} delivery is approaching!
</div>
<div class="deadline-box">
<div style="font-size: 36px; font-weight: bold;">{{ days_remaining }} Days</div>
<div>Cutoff Date: {{ cutoff_date }}</div>
</div>
<p>Next delivery: <strong>{{ next_delivery_date }}</strong></p>
<div class="current-address">
<strong>Current Delivery Address:</strong><br>{{ current_address }}
</div>
<div style="text-align: center;">
<a href="{{ update_address_url }}" class="cta-button">Update Address Now</a>
</div>
</div>
<div class="footer">
<p>Lavish Library | support@lavish-library.com</p>
</div>
</div>
</body>
</html>''',
                'plain_text_content': '''Address Change Deadline

Hi {{ customer_name }},

IMPORTANT: Address change deadline for your {{ subscription_name }} delivery is approaching!

Time Remaining: {{ days_remaining }} DAYS
Cutoff Date: {{ cutoff_date }}

Next delivery: {{ next_delivery_date }}

Current Delivery Address:
{{ current_address }}

Update your address: {{ update_address_url }}

Lavish Library | support@lavish-library.com''',
                'variables': {
                    'customer_name': 'Sarah',
                    'subscription_name': 'Premium Monthly Box',
                    'days_remaining': '3',
                    'cutoff_date': 'January 24, 2025',
                    'next_delivery_date': 'February 1, 2025',
                    'current_address': '123 Main Street, London, UK',
                    'update_address_url': 'https://7fa66c-ac.myshopify.com/account',
                },
                'is_active': True,
                'configuration': config
            }
        )
        
        if created:
            templates_created += 1
            self.stdout.write(self.style.SUCCESS(f'Created: {template.name}'))
        else:
            templates_updated += 1
            self.stdout.write(self.style.WARNING(f'Updated: {template.name}'))
        
        # Template 4: Renewal Notice
        template, created = EmailTemplate.objects.update_or_create(
            name='subscription_renewal_notice',
            defaults={
                'template_type': 'custom',
                'subject': 'Upcoming Renewal - {{ subscription_name }} on {{ renewal_date }}',
                'html_content': '''<!DOCTYPE html>
<html>
<head>
<style>
body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
.container { max-width: 600px; margin: 0 auto; padding: 20px; }
.header { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
.header h1 { margin: 0; font-size: 28px; }
.content { background: #fff; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.renewal-box { background: #e3f2fd; border-left: 4px solid #2196f3; padding: 15px; margin: 20px 0; border-radius: 5px; }
.charges-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
.charges-table td { padding: 12px; border-bottom: 1px solid #dee2e6; }
.charges-table tr:last-child td { border-bottom: none; font-weight: bold; background: #ecfdf5; }
.info-box { background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }
.cta-button { display: inline-block; background: #2196f3; color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; margin: 20px 0; font-weight: bold; }
.footer { text-align: center; margin-top: 30px; color: #666; font-size: 14px; }
</style>
</head>
<body>
<div class="container">
<div class="header">
<h1>Upcoming Renewal</h1>
</div>
<div class="content">
<p>Hi {{ customer_name }},</p>
<p>Your <strong>{{ subscription_name }}</strong> subscription will renew soon.</p>
<div class="renewal-box">
<strong>Renewal Date:</strong> {{ renewal_date }}<br>
<strong>Days Until Renewal:</strong> {{ days_until_renewal }} days
</div>
<table class="charges-table">
<tr><td>{{ subscription_name }}</td><td style="text-align: right;">£{{ subscription_cost }}</td></tr>
<tr><td>Shipping</td><td style="text-align: right;">£{{ shipping_cost }}</td></tr>
<tr><td><strong>Total Charge</strong></td><td style="text-align: right; color: #10b981; font-size: 20px;">£{{ total_cost }}</td></tr>
</table>
<div class="info-box">
<strong>Payment Method:</strong> {{ payment_method }}<br>
<strong>Delivery Address:</strong> {{ delivery_address }}
</div>
<div style="text-align: center;">
<a href="{{ manage_subscription_url }}" class="cta-button">Manage Subscription</a>
</div>
</div>
<div class="footer">
<p>Lavish Library | support@lavish-library.com</p>
</div>
</div>
</body>
</html>''',
                'plain_text_content': '''Upcoming Renewal - {{ subscription_name }}

Hi {{ customer_name }},

Your {{ subscription_name }} subscription will renew soon.

Renewal Date: {{ renewal_date }}
Days Until Renewal: {{ days_until_renewal }} days

CHARGES:
{{ subscription_name }}    £{{ subscription_cost }}
Shipping                  £{{ shipping_cost }}
-------------------------------------
TOTAL CHARGE             £{{ total_cost }}

Payment Method: {{ payment_method }}
Delivery Address: {{ delivery_address }}

Manage your subscription: {{ manage_subscription_url }}

Lavish Library | support@lavish-library.com''',
                'variables': {
                    'customer_name': 'Emma',
                    'subscription_name': 'Premium Monthly Box',
                    'renewal_date': 'February 1, 2025',
                    'days_until_renewal': '7',
                    'subscription_cost': '21.00',
                    'shipping_cost': '16.90',
                    'total_cost': '37.90',
                    'payment_method': 'Card ending in 5678',
                    'delivery_address': '456 Oak Avenue, Manchester, UK',
                    'manage_subscription_url': 'https://7fa66c-ac.myshopify.com/account',
                },
                'is_active': True,
                'configuration': config
            }
        )
        
        if created:
            templates_created += 1
            self.stdout.write(self.style.SUCCESS(f'Created: {template.name}'))
        else:
            templates_updated += 1
            self.stdout.write(self.style.WARNING(f'Updated: {template.name}'))
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(
            f'\nComplete! Created {templates_created}, Updated {templates_updated} templates\n'
        ))
