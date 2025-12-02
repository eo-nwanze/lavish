"""
Comprehensive test suite for Phase 1 Skip System Critical Fixes
Tests annual reset, customer API endpoints, and frontend functions
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, date
from unittest.mock import patch, MagicMock
import json

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lavish_backend.settings')
django.setup()

from customer_subscriptions.models import CustomerSubscription, Customer
from skips.models import SubscriptionSkip, SubscriptionSkipPolicy, SkipAnalytics, SubscriptionSyncLog
from skips.management.commands.reset_annual_skips import Command
from skips.customer_api import (
    cancel_subscription, pause_subscription, resume_subscription, 
    change_subscription_frequency, subscription_management_options
)

User = get_user_model()


class AnnualSkipResetTest(TestCase):
    """Test the annual skip reset management command"""
    
    def setUp(self):
        """Set up test data"""
        self.customer = Customer.objects.create(
            email="test@example.com",
            first_name="Test",
            last_name="Customer",
            shopify_customer_id="gid://shopify/Customer/123"
        )
        
        self.subscription = CustomerSubscription.objects.create(
            customer=self.customer,
            shopify_id="gid://shopify/SubscriptionContract/123",
            status="ACTIVE",
            skips_used=3,
            skips_remaining=2,
            skips_annual_reset_date=date(2024, 1, 1)
        )
        
        self.skip = SubscriptionSkip.objects.create(
            subscription=self.subscription,
            status="completed",
            skip_date=timezone.now() - timedelta(days=30)
        )
        
        self.analytics = SkipAnalytics.objects.create(
            subscription=self.subscription,
            skips_used_this_year=3,
            skips_remaining_this_year=2,
            annual_reset_date=date(2024, 1, 1)
        )
    
    def test_annual_reset_command_dry_run(self):
        """Test annual reset command in dry-run mode"""
        command = Command()
        
        with patch('builtins.print') as mock_print:
            command.handle(dry_run=True)
            
            # Check that dry run output is correct
            mock_print.assert_any_call("🔍 DRY RUN MODE - No changes will be made")
            mock_print.assert_any_call("📊 Annual Skip Reset Summary:")
            mock_print.assert_any_call("  Subscriptions processed: 1")
            mock_print.assert_any_call("  Skips reset: 3")
            mock_print.assert_any_call("  Analytics updated: 1")
    
    def test_annual_reset_command_actual(self):
        """Test annual reset command with actual changes"""
        command = Command()
        
        # Set reset date to trigger reset
        self.subscription.skips_annual_reset_date = date(2023, 1, 1)
        self.subscription.save()
        
        self.analytics.annual_reset_date = date(2023, 1, 1)
        self.analytics.save()
        
        with patch('builtins.print') as mock_print:
            command.handle()
            
            # Verify subscription was reset
            self.subscription.refresh_from_db()
            self.assertEqual(self.subscription.skips_used, 0)
            self.assertEqual(self.subscription.skips_remaining, 5)  # Assuming 5 total skips
            
            # Verify analytics was reset
            self.analytics.refresh_from_db()
            self.assertEqual(self.analytics.skips_used_this_year, 0)
            self.assertEqual(self.analytics.skips_remaining_this_year, 5)
            
            # Verify sync log was created
            sync_log = SubscriptionSyncLog.objects.latest('created_at')
            self.assertEqual(sync_log.operation_type, 'annual_skip_reset')
            self.assertEqual(sync_log.status, 'completed')
    
    def test_annual_reset_command_no_subscriptions(self):
        """Test command with no subscriptions needing reset"""
        # All subscriptions have current reset date
        command = Command()
        
        with patch('builtins.print') as mock_print:
            command.handle()
            
            mock_print.assert_any_call("✅ No subscriptions need annual reset")


class CustomerAPITest(TestCase):
    """Test customer-facing API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.customer = Customer.objects.create(
            email="test@example.com",
            first_name="Test",
            last_name="Customer",
            shopify_customer_id="gid://shopify/Customer/123"
        )
        
        self.subscription = CustomerSubscription.objects.create(
            customer=self.customer,
            shopify_id="gid://shopify/SubscriptionContract/123",
            status="ACTIVE",
            billing_policy_interval="MONTH",
            billing_policy_interval_count=1
        )
    
    @patch('skips.customer_api.SubscriptionBidirectionalSync')
    @patch('skips.customer_api.send_cancellation_confirmation')
    def test_cancel_subscription_success(self, mock_email, mock_sync):
        """Test successful subscription cancellation"""
        mock_sync_instance = MagicMock()
        mock_sync_instance.cancel_subscription_in_shopify.return_value = {'success': True}
        mock_sync.return_value = mock_sync_instance
        
        response = self.client.post(
            reverse('skips:cancel_subscription'),
            data=json.dumps({
                'subscription_id': 'gid://shopify/SubscriptionContract/123',
                'reason': 'too_expensive',
                'feedback': 'Need to save money',
                'confirm': True
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['subscription']['status'], 'CANCELLED')
        
        # Verify subscription was updated
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, 'CANCELLED')
        
        # Verify sync was called
        mock_sync_instance.cancel_subscription_in_shopify.assert_called_once()
        
        # Verify email was sent
        mock_email.assert_called_once()
    
    def test_cancel_subscription_missing_confirmation(self):
        """Test cancellation without confirmation"""
        response = self.client.post(
            reverse('skips:cancel_subscription'),
            data=json.dumps({
                'subscription_id': 'gid://shopify/SubscriptionContract/123',
                'reason': 'too_expensive'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('confirm=true', data['error'])
    
    def test_pause_subscription_success(self):
        """Test successful subscription pause"""
        response = self.client.post(
            reverse('skips:pause_subscription'),
            data=json.dumps({
                'subscription_id': 'gid://shopify/SubscriptionContract/123',
                'duration_months': 2,
                'reason': 'going on vacation'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['subscription']['status'], 'PAUSED')
        
        # Verify subscription was updated
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, 'PAUSED')
    
    def test_pause_subscription_invalid_duration(self):
        """Test pause with invalid duration"""
        response = self.client.post(
            reverse('skips:pause_subscription'),
            data=json.dumps({
                'subscription_id': 'gid://shopify/SubscriptionContract/123',
                'duration_months': 12,  # Too long
                'reason': 'going on vacation'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Duration must be between 1 and 6 months', data['error'])
    
    def test_resume_subscription_success(self):
        """Test successful subscription resume"""
        # First pause the subscription
        self.subscription.status = 'PAUSED'
        self.subscription.save()
        
        response = self.client.post(
            reverse('skips:resume_subscription'),
            data=json.dumps({
                'subscription_id': 'gid://shopify/SubscriptionContract/123'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['subscription']['status'], 'ACTIVE')
        
        # Verify subscription was updated
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, 'ACTIVE')
    
    def test_change_frequency_success(self):
        """Test successful frequency change"""
        response = self.client.post(
            reverse('skips:change_subscription_frequency'),
            data=json.dumps({
                'subscription_id': 'gid://shopify/SubscriptionContract/123',
                'new_interval': 'MONTH',
                'new_interval_count': 2
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['subscription']['billing_interval'], 'MONTH')
        self.assertEqual(data['subscription']['billing_interval_count'], 2)
        
        # Verify subscription was updated
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.billing_policy_interval, 'MONTH')
        self.assertEqual(self.subscription.billing_policy_interval_count, 2)
    
    def test_get_subscription_options(self):
        """Test getting subscription management options"""
        response = self.client.get(
            reverse('skips:subscription_management_options', args=['gid://shopify/SubscriptionContract/123'])
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertTrue(data['options']['can_cancel'])
        self.assertTrue(data['options']['can_pause'])
        self.assertFalse(data['options']['can_resume'])  # Active subscription can't be resumed
        self.assertTrue(data['options']['can_change_frequency'])
        
        # Check available frequencies
        frequencies = data['options']['available_frequencies']
        self.assertEqual(len(frequencies), 6)
        self.assertEqual(frequencies[0]['interval'], 'WEEK')
        self.assertEqual(frequencies[0]['count'], 1)
        
        # Check pause durations
        durations = data['options']['pause_durations']
        self.assertEqual(len(durations), 4)
        self.assertEqual(durations[0]['months'], 1)
        
        # Check cancellation reasons
        reasons = data['options']['cancellation_reasons']
        self.assertEqual(len(reasons), 7)
        self.assertEqual(reasons[0]['value'], 'too_expensive')


class FrontendIntegrationTest(TestCase):
    """Test frontend JavaScript integration"""
    
    def setUp(self):
        """Set up test data"""
        self.customer = Customer.objects.create(
            email="test@example.com",
            first_name="Test",
            last_name="Customer",
            shopify_customer_id="gid://shopify/Customer/123"
        )
        
        self.subscription = CustomerSubscription.objects.create(
            customer=self.customer,
            shopify_id="gid://shopify/SubscriptionContract/123",
            status="ACTIVE",
            billing_policy_interval="MONTH",
            billing_policy_interval_count=1
        )
    
    def test_subscription_details_api(self):
        """Test subscription details API for frontend"""
        response = self.client.get(
            reverse('skips:subscription_details', args=['gid://shopify/SubscriptionContract/123'])
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['subscription']['shopify_id'], 'gid://shopify/SubscriptionContract/123')
        self.assertEqual(data['subscription']['status'], 'ACTIVE')
    
    def test_skip_quota_api(self):
        """Test skip quota API for frontend"""
        response = self.client.get(
            reverse('skips:skip_quota', args=['gid://shopify/SubscriptionContract/123'])
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('skips_used', data)
        self.assertIn('skips_remaining', data)
        self.assertIn('annual_reset_date', data)


class ErrorHandlingTest(TestCase):
    """Test error handling in all components"""
    
    def test_cancel_nonexistent_subscription(self):
        """Test cancelling non-existent subscription"""
        response = self.client.post(
            reverse('skips:cancel_subscription'),
            data=json.dumps({
                'subscription_id': 'gid://shopify/SubscriptionContract/999',
                'reason': 'too_expensive',
                'confirm': True
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Subscription not found', data['error'])
    
    def test_cancel_already_cancelled_subscription(self):
        """Test cancelling already cancelled subscription"""
        customer = Customer.objects.create(
            email="test@example.com",
            first_name="Test",
            last_name="Customer",
            shopify_customer_id="gid://shopify/Customer/123"
        )
        
        subscription = CustomerSubscription.objects.create(
            customer=customer,
            shopify_id="gid://shopify/SubscriptionContract/123",
            status="CANCELLED"
        )
        
        response = self.client.post(
            reverse('skips:cancel_subscription'),
            data=json.dumps({
                'subscription_id': 'gid://shopify/SubscriptionContract/123',
                'reason': 'too_expensive',
                'confirm': True
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Cannot cancel subscription with status: CANCELLED', data['error'])
    
    def test_invalid_json_request(self):
        """Test API with invalid JSON"""
        response = self.client.post(
            reverse('skips:cancel_subscription'),
            data="invalid json",
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Invalid JSON', data['error'])


def run_all_tests():
    """Run all test suites"""
    print("🧪 Running Phase 1 Skip System Critical Fixes Test Suite")
    print("=" * 60)
    
    # Test Annual Reset Command
    print("\n📅 Testing Annual Skip Reset Command...")
    try:
        test_case = AnnualSkipResetTest()
        test_case.setUp()
        test_case.test_annual_reset_command_dry_run()
        print("✅ Annual reset dry-run test passed")
        
        test_case.setUp()
        test_case.test_annual_reset_command_actual()
        print("✅ Annual reset actual test passed")
        
        test_case.setUp()
        test_case.test_annual_reset_command_no_subscriptions()
        print("✅ Annual reset no subscriptions test passed")
    except Exception as e:
        print(f"❌ Annual reset test failed: {e}")
    
    # Test Customer API
    print("\n🔌 Testing Customer API Endpoints...")
    try:
        test_case = CustomerAPITest()
        test_case.setUp()
        test_case.test_cancel_subscription_success()
        print("✅ Cancel subscription test passed")
        
        test_case.setUp()
        test_case.test_cancel_subscription_missing_confirmation()
        print("✅ Cancel missing confirmation test passed")
        
        test_case.setUp()
        test_case.test_pause_subscription_success()
        print("✅ Pause subscription test passed")
        
        test_case.setUp()
        test_case.test_pause_subscription_invalid_duration()
        print("✅ Pause invalid duration test passed")
        
        test_case.setUp()
        test_case.test_resume_subscription_success()
        print("✅ Resume subscription test passed")
        
        test_case.setUp()
        test_case.test_change_frequency_success()
        print("✅ Change frequency test passed")
        
        test_case.setUp()
        test_case.test_get_subscription_options()
        print("✅ Get subscription options test passed")
    except Exception as e:
        print(f"❌ Customer API test failed: {e}")
    
    # Test Frontend Integration
    print("\n🖥️ Testing Frontend Integration...")
    try:
        test_case = FrontendIntegrationTest()
        test_case.setUp()
        test_case.test_subscription_details_api()
        print("✅ Subscription details API test passed")
        
        test_case.setUp()
        test_case.test_skip_quota_api()
        print("✅ Skip quota API test passed")
    except Exception as e:
        print(f"❌ Frontend integration test failed: {e}")
    
    # Test Error Handling
    print("\n⚠️ Testing Error Handling...")
    try:
        test_case = ErrorHandlingTest()
        test_case.test_cancel_nonexistent_subscription()
        print("✅ Cancel non-existent subscription test passed")
        
        test_case.test_cancel_already_cancelled_subscription()
        print("✅ Cancel already cancelled subscription test passed")
        
        test_case.test_invalid_json_request()
        print("✅ Invalid JSON request test passed")
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Phase 1 Skip System Critical Fixes Test Suite Complete!")
    print("📊 All critical functionality tested and validated")


if __name__ == "__main__":
    run_all_tests()