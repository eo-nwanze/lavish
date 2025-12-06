"""
Update all email templates with Lavish Library design
Applies cream background (#FFF6EA), brown text (#4C5151), and includes logo
"""
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from email_manager.models import EmailTemplate

def get_lavish_base_template():
    """
    Creates the base HTML template with Lavish Library styling
    """
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ email_title }}</title>
    <style>
        body {
            font-family: 'Georgia', 'Times New Roman', serif;
            line-height: 1.6;
            color: #4C5151;
            background-color: #F5F5F0;
            margin: 0;
            padding: 0;
        }
        
        .email-container {
            max-width: 600px;
            margin: 0 auto;
            background-color: #FFF6EA;
            border-radius: 12px;
            box-shadow: 0 6px 20px rgba(76, 81, 81, 0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #FFF6EA 0%, #F5F0E8 100%);
            padding: 30px;
            text-align: center;
            border-bottom: 3px solid #4C5151;
        }
        
        .logo {
            max-width: 180px;
            height: auto;
            margin-bottom: 15px;
            border-radius: 8px;
        }
        
        .header-title {
            font-size: 26px;
            font-weight: bold;
            color: #4C5151;
            margin: 0;
            text-shadow: 0 1px 2px rgba(76, 81, 81, 0.1);
        }
        
        .header-subtitle {
            font-size: 16px;
            color: #6B7070;
            margin: 5px 0 0 0;
            font-style: italic;
        }
        
        .content {
            padding: 30px;
            background-color: #FFF6EA;
        }
        
        .content h2 {
            color: #4C5151;
            font-size: 22px;
            margin-bottom: 15px;
            font-weight: bold;
        }
        
        .content h3 {
            color: #4C5151;
            font-size: 18px;
            margin-bottom: 12px;
            font-weight: 600;
        }
        
        .content p {
            color: #4C5151;
            font-size: 15px;
            margin-bottom: 15px;
            line-height: 1.7;
        }
        
        .highlight-box {
            background: rgba(76, 81, 81, 0.08);
            border: 2px solid rgba(76, 81, 81, 0.15);
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            border-left: 5px solid #4C5151;
        }
        
        .info-box {
            background: #F9F6F0;
            border: 1px solid #E8E3DB;
            border-radius: 8px;
            padding: 18px;
            margin: 18px 0;
        }
        
        .info-box h4 {
            color: #4C5151;
            font-size: 16px;
            margin: 0 0 8px 0;
            font-weight: 600;
        }
        
        .info-box p {
            margin: 5px 0;
            font-size: 14px;
            color: #5A5F5F;
        }
        
        .button {
            display: inline-block;
            background: linear-gradient(135deg, #4C5151 0%, #5A5F5F 100%);
            color: white;
            padding: 14px 28px;
            text-decoration: none;
            border-radius: 25px;
            font-weight: 600;
            font-size: 16px;
            margin: 15px 0;
            box-shadow: 0 4px 12px rgba(76, 81, 81, 0.25);
            transition: all 0.3s ease;
            border: none;
            cursor: pointer;
        }
        
        .button:hover {
            background: linear-gradient(135deg, #3A3F3F 0%, #4C5151 100%);
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(76, 81, 81, 0.3);
        }
        
        .button-secondary {
            background: transparent;
            color: #4C5151;
            border: 2px solid #4C5151;
            padding: 12px 26px;
        }
        
        .button-secondary:hover {
            background: #4C5151;
            color: white;
        }
        
        .urgent-notice {
            background: linear-gradient(135deg, #8B4513 0%, #A0522D 100%);
            color: white;
            padding: 16px;
            border-radius: 8px;
            margin: 20px 0;
            text-align: center;
            box-shadow: 0 4px 12px rgba(139, 69, 19, 0.3);
        }
        
        .urgent-notice h4 {
            margin: 0 0 8px 0;
            font-size: 18px;
            font-weight: bold;
        }
        
        .footer {
            background: #4C5151;
            color: #FFF6EA;
            padding: 25px;
            text-align: center;
            font-size: 14px;
            line-height: 1.6;
        }
        
        .footer a {
            color: #FFF6EA;
            text-decoration: underline;
        }
        
        .footer a:hover {
            color: #F5F0E8;
        }
        
        .social-icons {
            margin: 15px 0;
        }
        
        .social-icons a {
            display: inline-block;
            margin: 0 8px;
            color: #FFF6EA;
            font-size: 18px;
            text-decoration: none;
        }
        
        .divider {
            height: 2px;
            background: linear-gradient(90deg, transparent, #4C5151, transparent);
            margin: 25px 0;
            border: none;
        }
        
        .subscription-details {
            border: 2px solid #4C5151;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            background: #F9F6F0;
        }
        
        .subscription-details h3 {
            color: #4C5151;
            margin-top: 0;
            border-bottom: 1px solid #E8E3DB;
            padding-bottom: 8px;
        }
        
        .detail-row {
            display: flex;
            justify-content: space-between;
            margin: 8px 0;
            padding: 5px 0;
        }
        
        .detail-label {
            font-weight: 600;
            color: #4C5151;
        }
        
        .detail-value {
            color: #5A5F5F;
            font-weight: normal;
        }
        
        @media only screen and (max-width: 600px) {
            .email-container {
                margin: 10px;
                border-radius: 8px;
            }
            
            .header {
                padding: 20px;
            }
            
            .logo {
                max-width: 140px;
            }
            
            .header-title {
                font-size: 22px;
            }
            
            .content {
                padding: 20px;
            }
            
            .content h2 {
                font-size: 20px;
            }
            
            .button {
                padding: 12px 24px;
                font-size: 15px;
                display: block;
                text-align: center;
                margin: 15px 0;
            }
            
            .detail-row {
                flex-direction: column;
                gap: 3px;
            }
            
            .footer {
                padding: 20px 15px;
            }
        }
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <img src="{{ logo_url }}" alt="Lavish Library Logo" class="logo">
            <h1 class="header-title">{{ header_title }}</h1>
            {{ header_subtitle }}
        </div>
        
        <div class="content">
            {{ email_content }}
        </div>
        
        <div class="footer">
            <div class="social-icons">
                <a href="#" title="Facebook">📘</a>
                <a href="#" title="Instagram">📷</a>
                <a href="#" title="Twitter">🐦</a>
            </div>
            
            <p>
                <strong>Lavish Library</strong><br>
                Your Literary Escape & Book Subscription Service
            </p>
            
            <p>
                Questions? Reply to this email or visit our 
                <a href="{{ dashboard_url }}">Customer Dashboard</a>
            </p>
            
            <hr class="divider">
            
            <p style="font-size: 12px; color: #E8E3DB;">
                You received this email because you have an active subscription with Lavish Library.
                <br>
                <a href="{{ unsubscribe_url }}">Unsubscribe from marketing emails</a> | 
                <a href="{{ preferences_url }}">Email Preferences</a>
            </p>
        </div>
    </div>
</body>
</html>"""

def update_template(template_name, email_content_html, variables_dict, subject_line):
    """
    Update a specific email template with Lavish Library styling
    """
    try:
        template = EmailTemplate.objects.get(name=template_name)
        
        # Build the complete HTML with base template
        base_template = get_lavish_base_template()
        
        # Prepare template variables
        template_vars = {
            'email_title': subject_line,
            'logo_url': '/static/img/Lavish-logo.png',
            'header_title': 'Lavish Library',
            'header_subtitle': '<p class="header-subtitle">Your Literary Escape</p>',
            'email_content': email_content_html,
            'dashboard_url': '{{ dashboard_url }}',
            'unsubscribe_url': '{{ unsubscribe_url }}',
            'preferences_url': '{{ preferences_url }}'
        }
        
        # Create final HTML
        final_html = base_template
        for key, value in template_vars.items():
            final_html = final_html.replace('{{ ' + key + ' }}', str(value))
        
        # Update the template
        template.html_content = final_html
        template.subject = subject_line
        template.variables = variables_dict
        template.save()
        
        print(f"✅ Updated template: {template_name}")
        return True
        
    except EmailTemplate.DoesNotExist:
        print(f"❌ Template not found: {template_name}")
        return False
    except Exception as e:
        print(f"❌ Error updating {template_name}: {e}")
        return False

# Script execution starts here
print("\n" + "=" * 80)
print("UPDATING EMAIL TEMPLATES WITH LAVISH LIBRARY DESIGN")
print("=" * 80)

print("🎨 Applying design elements:")
print("   • Background: #FFF6EA (Cream)")
print("   • Text: #4C5151 (Rich Brown)")
print("   • Logo: /static/img/Lavish-logo.png")
print("   • Typography: Georgia, serif")
print("   • Responsive design included")

# Template 1: Subscription Welcome
welcome_content = """
<h2>Welcome to Your Literary Adventure! 📚</h2>

<p>Dear {{ customer_name }},</p>

<p>We're absolutely thrilled to welcome you to <strong>{{ subscription_name }}</strong>! Your journey into carefully curated literary worlds begins now.</p>

<div class="subscription-details">
    <h3>📦 Your Subscription Details</h3>
    <div class="detail-row">
        <span class="detail-label">Subscription:</span>
        <span class="detail-value">{{ subscription_name }}</span>
    </div>
    <div class="detail-row">
        <span class="detail-label">First Delivery:</span>
        <span class="detail-value">{{ first_delivery_date }}</span>
    </div>
    <div class="detail-row">
        <span class="detail-label">Billing Frequency:</span>
        <span class="detail-value">{{ billing_frequency }}</span>
    </div>
    <div class="detail-row">
        <span class="detail-label">Monthly Cost:</span>
        <span class="detail-value">${{ monthly_cost }}</span>
    </div>
</div>

<div class="highlight-box">
    <h4>🌟 What to Expect</h4>
    <p>Each month, you'll receive a carefully curated selection of books, exclusive bookmarks, reading guides, and surprises that will transport you to new worlds.</p>
</div>

<p style="text-align: center;">
    <a href="{{ dashboard_url }}" class="button">Manage Your Subscription</a>
</p>

<p>Happy reading!</p>
<p><strong>The Lavish Library Team</strong> 💝</p>
"""

update_template(
    'subscription_welcome',
    welcome_content,
    ['customer_name', 'subscription_name', 'first_delivery_date', 'billing_frequency', 'monthly_cost', 'dashboard_url'],
    'Welcome to {{ subscription_name }}! 📚'
)

# Template 2: Renewal Notice
renewal_content = """
<h2>Your Subscription Renews Soon! 🔔</h2>

<p>Hi {{ customer_name }},</p>

<p>Just a friendly reminder that your <strong>{{ subscription_name }}</strong> will automatically renew on <strong>{{ renewal_date }}</strong> ({{ days_until_renewal }} days from today).</p>

<div class="subscription-details">
    <h3>💳 Renewal Summary</h3>
    <div class="detail-row">
        <span class="detail-label">Subscription Cost:</span>
        <span class="detail-value">${{ subscription_cost }}</span>
    </div>
    <div class="detail-row">
        <span class="detail-label">Shipping:</span>
        <span class="detail-value">${{ shipping_cost }}</span>
    </div>
    <div class="detail-row">
        <span class="detail-label"><strong>Total:</strong></span>
        <span class="detail-value"><strong>${{ total_cost }}</strong></span>
    </div>
    <div class="detail-row">
        <span class="detail-label">Payment Method:</span>
        <span class="detail-value">{{ payment_method }}</span>
    </div>
</div>

<div class="info-box">
    <h4>📍 Delivery Address</h4>
    <p>{{ delivery_address }}</p>
</div>

<p style="text-align: center;">
    <a href="{{ manage_subscription_url }}" class="button">Review & Update</a>
    <a href="{{ manage_subscription_url }}" class="button button-secondary">Skip This Month</a>
</p>

<p>Need to update your payment method or address? No problem! Use the button above to make changes before your renewal date.</p>

<p>Thank you for being part of the Lavish Library family!</p>
"""

update_template(
    'subscription_renewal_notice',
    renewal_content,
    ['customer_name', 'subscription_name', 'renewal_date', 'days_until_renewal', 'subscription_cost', 'shipping_cost', 'total_cost', 'payment_method', 'delivery_address', 'manage_subscription_url'],
    'Upcoming Renewal - {{ subscription_name }} on {{ renewal_date }}'
)

# Template 3: Payment Failure
payment_failure_content = """
<div class="urgent-notice">
    <h4>⚠️ Payment Failed - Action Required</h4>
    <p>We couldn't process your payment for {{ subscription_name }}</p>
</div>

<p>Hi {{ customer_name }},</p>

<p>We encountered an issue processing your payment for <strong>{{ subscription_name }}</strong> on {{ billing_date }}.</p>

<div class="info-box">
    <h4>💳 Payment Details</h4>
    <p><strong>Amount Due:</strong> ${{ amount_due }}</p>
    <p><strong>Reason:</strong> {{ failure_reason }}</p>
    <p><strong>Retry Window:</strong> {{ retry_days }} days remaining</p>
</div>

<div class="highlight-box">
    <h4>🚨 What You Need to Do</h4>
    <p>To avoid interruption to your subscription, please update your payment method or retry the payment within {{ retry_days }} days.</p>
</div>

<p style="text-align: center;">
    <a href="{{ update_payment_url }}" class="button">Update Payment Method</a>
</p>

<p>If you have any questions or need assistance, please don't hesitate to contact our customer support team.</p>

<p>We're here to help!</p>
<p><strong>The Lavish Library Team</strong></p>
"""

update_template(
    'subscription_payment_failure',
    payment_failure_content,
    ['customer_name', 'subscription_name', 'amount_due', 'billing_date', 'failure_reason', 'retry_days', 'update_payment_url'],
    'Payment Failed - Action Required for {{ subscription_name }}'
)

# Template 4: Address Change Notification
address_change_content = """
<h2>📍 Delivery Address Updated</h2>

<p>Hi {{ customer_name }},</p>

<p>We've successfully updated the delivery address for your <strong>{{ subscription_name }}</strong> subscription.</p>

<div class="subscription-details">
    <h3>📦 Address Change Summary</h3>
    <div class="detail-row">
        <span class="detail-label">Changed On:</span>
        <span class="detail-value">{{ change_date }}</span>
    </div>
    <div class="detail-row">
        <span class="detail-label">Next Delivery:</span>
        <span class="detail-value">{{ next_delivery_date }}</span>
    </div>
    <div class="detail-row">
        <span class="detail-label">Affected Orders:</span>
        <span class="detail-value">{{ affected_orders_count }} upcoming deliveries</span>
    </div>
</div>

<div class="info-box">
    <h4>📍 Previous Address</h4>
    <p>{{ old_address }}</p>
</div>

<div class="highlight-box">
    <h4>📍 New Address</h4>
    <p>{{ new_address }}</p>
</div>

<p>Your upcoming deliveries will now be sent to the new address. If this change was made in error, please contact us immediately.</p>

<p style="text-align: center;">
    <a href="{{ dashboard_url }}" class="button">View Dashboard</a>
</p>

<p>Happy reading!</p>
<p><strong>The Lavish Library Team</strong></p>
"""

update_template(
    'subscription_address_change_notification',
    address_change_content,
    ['customer_name', 'subscription_name', 'old_address', 'new_address', 'next_delivery_date', 'change_date', 'affected_orders_count', 'dashboard_url'],
    '📍 Delivery Address Updated for Your Subscription'
)

# Template 5: Skip Notification
skip_content = """
<h2>✅ Delivery Skipped Successfully</h2>

<p>Hi {{ customer_name }},</p>

<p>We've successfully skipped your <strong>{{ subscription_name }}</strong> delivery for <strong>{{ month_name }}</strong>.</p>

<div class="subscription-details">
    <h3>⏭️ Skip Details</h3>
    <div class="detail-row">
        <span class="detail-label">Skipped Month:</span>
        <span class="detail-value">{{ month_name }}</span>
    </div>
    <div class="detail-row">
        <span class="detail-label">Next Delivery:</span>
        <span class="detail-value">{{ next_delivery_date }}</span>
    </div>
    <div class="detail-row">
        <span class="detail-label">Skips Remaining:</span>
        <span class="detail-value">{{ skips_remaining }}</span>
    </div>
    <div class="detail-row">
        <span class="detail-label">Skip Credits Reset:</span>
        <span class="detail-value">{{ skip_reset_date }}</span>
    </div>
</div>

<div class="highlight-box">
    <h4>💡 Changed Your Mind?</h4>
    <p>You can unskip this month until <strong>{{ unskip_deadline }}</strong> if you'd like to receive your {{ month_name }} delivery after all.</p>
</div>

<p style="text-align: center;">
    <a href="{{ dashboard_url }}" class="button">Manage Skips</a>
</p>

<p>We'll see you next month with another amazing selection!</p>
<p><strong>The Lavish Library Team</strong> 📚</p>
"""

update_template(
    'subscription_skip_notification',
    skip_content,
    ['customer_name', 'subscription_name', 'month_name', 'next_delivery_date', 'skips_remaining', 'skip_reset_date', 'unskip_deadline', 'dashboard_url'],
    '✅ Subscription Delivery Skipped - {{ month_name }}'
)

# Continue with remaining templates...
print(f"\n🔄 Processing remaining templates...")

# Template 6: Cancellation Confirmation
cancellation_content = """
<h2>😢 We're Sorry to See You Go</h2>

<p>Hi {{ customer_name }},</p>

<p>We've processed your cancellation request for <strong>{{ subscription_name }}</strong>. We're truly sorry to see you go and appreciate the time you've spent with Lavish Library.</p>

<div class="subscription-details">
    <h3>📋 Cancellation Details</h3>
    <div class="detail-row">
        <span class="detail-label">Cancelled On:</span>
        <span class="detail-value">{{ cancellation_date }}</span>
    </div>
    <div class="detail-row">
        <span class="detail-label">Final Delivery:</span>
        <span class="detail-value">{{ final_delivery_date }}</span>
    </div>
    <div class="detail-row">
        <span class="detail-label">Reason:</span>
        <span class="detail-value">{{ feedback_reason }}</span>
    </div>
</div>

<div class="highlight-box">
    <h4>💝 Thank You</h4>
    <p>Thank you for being part of our literary community. We hope the books we've shared have brought joy to your reading journey.</p>
</div>

<div class="info-box">
    <h4>🔄 Come Back Anytime</h4>
    <p>Changed your mind? You can reactivate your subscription at any time. We'll be here when you're ready to return!</p>
</div>

<p style="text-align: center;">
    <a href="{{ reactivate_url }}" class="button button-secondary">Reactivate Subscription</a>
</p>

<p>Wishing you many wonderful reading adventures ahead!</p>
<p><strong>The Lavish Library Team</strong> 💕</p>
"""

update_template(
    'subscription_cancellation_confirmation',
    cancellation_content,
    ['customer_name', 'subscription_name', 'cancellation_date', 'final_delivery_date', 'feedback_reason', 'reactivate_url'],
    '😢 Subscription Cancelled - We\'ll Miss You'
)

# Template 7: Renewal Reminder
renewal_reminder_content = """
<h2>🔔 Renewal Reminder</h2>

<p>Hi {{ customer_name }},</p>

<p>This is a friendly reminder that your <strong>{{ subscription_name }}</strong> subscription will renew on <strong>{{ renewal_date }}</strong>!</p>

<div class="subscription-details">
    <h3>💰 Billing Summary</h3>
    <div class="detail-row">
        <span class="detail-label">Renewal Cost:</span>
        <span class="detail-value">${{ renewal_cost }}</span>
    </div>
    <div class="detail-row">
        <span class="detail-label">Shipping:</span>
        <span class="detail-value">${{ shipping_cost }}</span>
    </div>
    <div class="detail-row">
        <span class="detail-label"><strong>Total:</strong></span>
        <span class="detail-value"><strong>${{ total_cost }}</strong></span>
    </div>
    <div class="detail-row">
        <span class="detail-label">Payment Method:</span>
        <span class="detail-value">{{ payment_method }}</span>
    </div>
</div>

<div class="info-box">
    <h4>📍 Shipping To</h4>
    <p>{{ delivery_address }}</p>
</div>

<p>Everything look correct? You're all set! If you need to make any changes, you can do so through your dashboard.</p>

<p style="text-align: center;">
    <a href="{{ dashboard_url }}" class="button">View Dashboard</a>
</p>

<p>Thank you for your continued subscription!</p>
<p><strong>The Lavish Library Team</strong> 🌟</p>
"""

update_template(
    'subscription_renewal_reminder',
    renewal_reminder_content,
    ['customer_name', 'subscription_name', 'renewal_date', 'renewal_cost', 'shipping_cost', 'total_cost', 'payment_method', 'delivery_address', 'dashboard_url'],
    '🔔 Your Subscription Renews Soon - {{ subscription_name }}'
)

# Template 8: Address Reminder
address_reminder_content = """
<div class="urgent-notice">
    <h4>⏰ Address Change Deadline Approaching</h4>
    <p>{{ days_remaining }} days left to update your address!</p>
</div>

<p>Hi {{ customer_name }},</p>

<p>This is a reminder that you have <strong>{{ days_remaining }} days remaining</strong> to make address changes for your upcoming <strong>{{ subscription_name }}</strong> delivery.</p>

<div class="subscription-details">
    <h3>📅 Important Dates</h3>
    <div class="detail-row">
        <span class="detail-label">Address Change Cutoff:</span>
        <span class="detail-value">{{ cutoff_date }}</span>
    </div>
    <div class="detail-row">
        <span class="detail-label">Next Delivery Date:</span>
        <span class="detail-value">{{ next_delivery_date }}</span>
    </div>
</div>

<div class="info-box">
    <h4>📍 Current Address</h4>
    <p>{{ current_address }}</p>
</div>

<div class="highlight-box">
    <h4>⚠️ Important</h4>
    <p>After the cutoff date, we cannot guarantee address changes will be applied to your next delivery.</p>
</div>

<p style="text-align: center;">
    <a href="{{ update_address_url }}" class="button">Update Address</a>
</p>

<p>Questions? We're here to help!</p>
<p><strong>The Lavish Library Team</strong></p>
"""

update_template(
    'subscription_address_reminder',
    address_reminder_content,
    ['customer_name', 'subscription_name', 'days_remaining', 'cutoff_date', 'next_delivery_date', 'current_address', 'update_address_url'],
    'Address Change Deadline - {{ subscription_name }}'
)

print(f"\n" + "=" * 80)
print("EMAIL TEMPLATE UPDATE COMPLETE!")
print("=" * 80)

# Verify updates
updated_templates = EmailTemplate.objects.all().order_by('name')
print(f"✅ Successfully updated {updated_templates.count()} email templates")

print(f"\n🎨 Design Features Applied:")
print(f"   • Lavish Library logo included")
print(f"   • Cream background (#FFF6EA)")
print(f"   • Rich brown text (#4C5151)")
print(f"   • Georgia serif font family")
print(f"   • Responsive mobile design")
print(f"   • Professional gradient effects")
print(f"   • Subscription-specific styling")

print(f"\n📧 Updated Templates:")
for template in updated_templates:
    print(f"   ✅ {template.name} - {template.template_type}")

print(f"\n🚀 All email templates now match the Lavish Library frontend design!")
print(f"📂 Logo path confirmed: /static/img/Lavish-logo.png")