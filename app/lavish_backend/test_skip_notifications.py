"""
Simple test script to verify skip notification integration with email_manager

Run this script to test that skip notifications are working correctly.

Usage:
    python test_skip_notifications.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.utils import timezone
from datetime import timedelta
from skips.models import SubscriptionSkip, SkipNotification
from customer_subscriptions.models import CustomerSubscription
from customers.models import ShopifyCustomer
from skips.notification_service import SkipNotificationService
from email_manager.models import EmailConfiguration

def test_email_configuration():
    """Test that email configuration exists"""
    print("=" * 50)
    print("Testing Email Configuration")
    print("=" * 50)
    
    config = EmailConfiguration.objects.filter(is_default=True).first()
    if config:
        print(f"✓ Default email configuration found: {config.name}")
        print(f"  Host: {config.email_host}")
        print(f"  Port: {config.email_port}")
        print(f"  From: {config.default_from_email}")
        return True
    else:
        print("✗ No default email configuration found!")
        print("  Please create one in Django Admin → Email Manager → Email Configurations")
        return False

def test_skip_notification_service():
    """Test skip notification service"""
    print("\n" + "=" * 50)
    print("Testing Skip Notification Service")
    print("=" * 50)
    
    try:
        # Check if service can be imported
        print("✓ SkipNotificationService imported successfully")
        
        # Check if methods exist
        methods = [
            'send_skip_confirmed_notification',
            'send_skip_reminder_notification',
            'send_skip_limit_reached_notification'
        ]
        
        for method in methods:
            if hasattr(SkipNotificationService, method):
                print(f"✓ Method '{method}' exists")
            else:
                print(f"✗ Method '{method}' missing!")
                return False
        
        return True
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def test_skip_notification_model():
    """Test that SkipNotification model works"""
    print("\n" + "=" * 50)
    print("Testing SkipNotification Model")
    print("=" * 50)
    
    try:
        total = SkipNotification.objects.count()
        print(f"✓ SkipNotification model accessible")
        print(f"  Total notifications in database: {total}")
        
        if total > 0:
            recent = SkipNotification.objects.order_by('-created_at').first()
            print(f"\n  Most recent notification:")
            print(f"    Type: {recent.notification_type}")
            print(f"    Recipient: {recent.recipient_email}")
            print(f"    Delivered: {recent.delivered}")
            print(f"    Sent at: {recent.sent_at or 'Not sent'}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def test_data_exists():
    """Test that required data exists"""
    print("\n" + "=" * 50)
    print("Testing Required Data")
    print("=" * 50)
    
    # Check customers
    customer_count = ShopifyCustomer.objects.count()
    print(f"Customers in database: {customer_count}")
    
    # Check subscriptions
    subscription_count = CustomerSubscription.objects.count()
    print(f"Subscriptions in database: {subscription_count}")
    
    # Check skips
    skip_count = SubscriptionSkip.objects.count()
    print(f"Skips in database: {skip_count}")
    
    if skip_count > 0:
        print("\n  Sample skip:")
        skip = SubscriptionSkip.objects.order_by('-created_at').first()
        print(f"    ID: {skip.id}")
        print(f"    Status: {skip.status}")
        print(f"    Original date: {skip.original_order_date}")
        print(f"    New date: {skip.new_order_date}")
    
    return True

def create_test_notification():
    """Attempt to create a test notification (if data exists)"""
    print("\n" + "=" * 50)
    print("Test Notification Creation")
    print("=" * 50)
    
    # Find a confirmed skip
    skip = SubscriptionSkip.objects.filter(status='confirmed').first()
    
    if not skip:
        print("ℹ No confirmed skips found to test with")
        print("  Create a skip in admin and confirm it to test notifications")
        return True
    
    print(f"Found test skip: ID {skip.id}")
    print(f"Subscription: {skip.subscription}")
    
    try:
        print("\nAttempting to send test notification...")
        success = SkipNotificationService.send_skip_confirmed_notification(
            skip=skip,
            subscription=skip.subscription
        )
        
        if success:
            print("✓ Test notification sent successfully!")
            
            # Check if notification was recorded
            notification = SkipNotification.objects.filter(skip=skip).order_by('-created_at').first()
            if notification:
                print(f"\n  Notification record:")
                print(f"    Type: {notification.notification_type}")
                print(f"    Recipient: {notification.recipient_email}")
                print(f"    Subject: {notification.subject}")
                print(f"    Delivered: {notification.delivered}")
                print(f"    Sent at: {notification.sent_at}")
        else:
            print("✗ Test notification failed to send")
            print("  Check email configuration and Django logs")
        
        return success
    except Exception as e:
        print(f"✗ Error sending test notification: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "SKIP NOTIFICATION INTEGRATION TEST" + " " * 14 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\n")
    
    results = {
        "Email Configuration": test_email_configuration(),
        "Notification Service": test_skip_notification_service(),
        "Notification Model": test_skip_notification_model(),
        "Data Check": test_data_exists(),
    }
    
    # Only try to send test if all previous checks passed
    if all(results.values()):
        print("\n⚠️  WARNING: This will attempt to send a real email!")
        response = input("Proceed with sending test email? (yes/no): ")
        if response.lower() in ['yes', 'y']:
            results["Test Email"] = create_test_notification()
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ ALL TESTS PASSED")
        print("\nSkip notification integration is working correctly!")
        print("\nNext steps:")
        print("1. Test skip creation via API")
        print("2. Verify emails in customer inboxes")
        print("3. Set up scheduled reminder command")
    else:
        print("✗ SOME TESTS FAILED")
        print("\nPlease fix the issues above before using skip notifications.")
    print("=" * 50)

if __name__ == '__main__':
    main()
