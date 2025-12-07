"""
Subscription Billing Automation Tasks
======================================

Scheduled tasks for automated subscription billing.
Based on: https://shopify.dev/docs/apps/build/purchase-options/subscriptions/billing-cycles

Tasks:
- Bill subscriptions daily
- Handle billing failures with retry logic
- Manage billing cycles
- Send customer notifications
"""

import logging
from datetime import date, datetime, timedelta
from django.utils import timezone
from django.db import transaction
from .models import CustomerSubscription, SubscriptionBillingAttempt, SubscriptionSyncLog
from .bidirectional_sync import subscription_sync
from .email_service import send_subscription_email
from dateutil.relativedelta import relativedelta

logger = logging.getLogger('customer_subscriptions.tasks')


class SubscriptionBillingAutomation:
    """Automated billing service for subscriptions"""
    
    def __init__(self):
        self.results = {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
    
    def bill_due_subscriptions(self, dry_run=False):
        """
        Bill all subscriptions due today
        
        This is the main function that should run daily via cron job
        
        Args:
            dry_run: If True, only simulate billing (no actual charges)
            
        Returns:
            Dict with results summary
        """
        today = date.today()
        
        # Find subscriptions due for billing
        subscriptions_due = CustomerSubscription.objects.filter(
            status='ACTIVE',
            next_billing_date__lte=today
        ).select_related('customer', 'selling_plan')
        
        self.results['total'] = subscriptions_due.count()
        
        logger.info(f"{'🔍 DRY RUN:' if dry_run else '💳 BILLING:'} Found {self.results['total']} subscriptions due")
        
        # Create sync log
        sync_log = SubscriptionSyncLog.objects.create(
            operation_type='bulk_sync',
            status='in_progress',
            started_at=timezone.now()
        )
        
        try:
            for subscription in subscriptions_due:
                result = self._bill_single_subscription(subscription, dry_run)
                
                if result['success']:
                    self.results['successful'] += 1
                elif result.get('skipped'):
                    self.results['skipped'] += 1
                else:
                    self.results['failed'] += 1
                    self.results['errors'].append(result)
            
            # Update sync log
            sync_log.status = 'completed'
            sync_log.subscriptions_processed = self.results['total']
            sync_log.subscriptions_successful = self.results['successful']
            sync_log.subscriptions_failed = self.results['failed']
            sync_log.completed_at = timezone.now()
            sync_log.error_details = self.results['errors']
            sync_log.save()
            
            logger.info(f"✅ Billing complete: {self.results['successful']}/{self.results['total']} successful")
            
            return self.results
            
        except Exception as e:
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.save()
            raise
    
    def _bill_single_subscription(self, subscription, dry_run=False):
        """Bill a single subscription"""
        customer_name = f"{subscription.customer.first_name} {subscription.customer.last_name}"
        
        logger.info(f"Processing: Subscription #{subscription.id} - {customer_name}")
        
        # Check if subscription has payment method
        if not subscription.payment_method_id:
            logger.warning(f"  ⚠️ No payment method - skipping")
            return {
                'success': False,
                'skipped': True,
                'subscription_id': subscription.id,
                'customer': customer_name,
                'reason': 'no_payment_method'
            }
        
        # Check if customer exists in Shopify
        if not subscription.customer.shopify_id:
            logger.warning(f"  ⚠️ Customer not synced to Shopify - skipping")
            return {
                'success': False,
                'skipped': True,
                'subscription_id': subscription.id,
                'customer': customer_name,
                'reason': 'customer_not_synced'
            }
        
        # Check if subscription exists in Shopify
        if not subscription.shopify_id:
            logger.warning(f"  ⚠️ Subscription not synced to Shopify - skipping")
            return {
                'success': False,
                'skipped': True,
                'subscription_id': subscription.id,
                'customer': customer_name,
                'reason': 'subscription_not_synced'
            }
        
        if dry_run:
            logger.info(f"  ✅ Would bill ${subscription.total_price} {subscription.currency}")
            return {'success': True, 'dry_run': True}
        
        # Create billing attempt
        result = subscription_sync.create_billing_attempt(subscription)
        
        if result.get('success'):
            logger.info(f"  ✅ Billed successfully - Order: {result.get('order_name', 'pending')}")
            return {
                'success': True,
                'subscription_id': subscription.id,
                'customer': customer_name,
                'order_id': result.get('order_id'),
                'order_name': result.get('order_name')
            }
        else:
            logger.error(f"  ❌ Billing failed: {result.get('message')}")
            
            # Handle billing failure
            self._handle_billing_failure(subscription, result.get('message', 'Unknown error'))
            
            return {
                'success': False,
                'subscription_id': subscription.id,
                'customer': customer_name,
                'error': result.get('message')
            }
    
    def _handle_billing_failure(self, subscription, error_message):
        """Handle billing failure with retry logic"""
        
        # Get recent billing attempts for this subscription
        recent_failures = SubscriptionBillingAttempt.objects.filter(
            subscription=subscription,
            status='FAILED',
            attempted_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        logger.warning(f"  Failure count in last 7 days: {recent_failures}")
        
        if recent_failures >= 3:
            # Max retries exceeded - pause subscription
            logger.error(f"  ⚠️ Max retries exceeded - pausing subscription")
            
            with transaction.atomic():
                subscription.status = 'FAILED'
                subscription.shopify_push_error = f"Billing failed after {recent_failures} attempts: {error_message}"
                subscription.save()
            
            # TODO: Send email to customer
            # send_subscription_email(
            #     subscription.customer.email,
            #     'billing_failed_max_retries',
            #     {'subscription': subscription, 'error': error_message}
            # )
        else:
            # Schedule retry in 2 days
            logger.info(f"  🔄 Will retry in 2 days (attempt {recent_failures + 1}/3)")
            
            # TODO: Send email to customer
            # send_subscription_email(
            #     subscription.customer.email,
            #     'billing_failed_retry',
            #     {'subscription': subscription, 'retry_date': date.today() + timedelta(days=2)}
            # )
    
    def retry_failed_billings(self):
        """Retry subscriptions with failed billing attempts"""
        
        # Find subscriptions with recent failures
        failed_attempts = SubscriptionBillingAttempt.objects.filter(
            status='FAILED',
            attempted_at__gte=timezone.now() - timedelta(days=7)
        ).select_related('subscription', 'subscription__customer')
        
        logger.info(f"🔄 Found {failed_attempts.count()} failed billing attempts to retry")
        
        results = {
            'total': 0,
            'successful': 0,
            'failed': 0
        }
        
        # Group by subscription (avoid duplicate retries)
        subscription_ids = set(fa.subscription_id for fa in failed_attempts)
        
        for subscription_id in subscription_ids:
            try:
                subscription = CustomerSubscription.objects.get(id=subscription_id)
                
                # Check failure count
                failure_count = SubscriptionBillingAttempt.objects.filter(
                    subscription=subscription,
                    status='FAILED',
                    attempted_at__gte=timezone.now() - timedelta(days=7)
                ).count()
                
                if failure_count >= 3:
                    logger.warning(f"  Skipping subscription {subscription_id} - max retries")
                    continue
                
                results['total'] += 1
                
                # Retry billing
                result = subscription_sync.create_billing_attempt(subscription)
                
                if result.get('success'):
                    results['successful'] += 1
                    logger.info(f"  ✅ Retry successful: {subscription_id}")
                else:
                    results['failed'] += 1
                    logger.error(f"  ❌ Retry failed: {subscription_id}")
                
            except CustomerSubscription.DoesNotExist:
                continue
        
        logger.info(f"✅ Retry complete: {results['successful']}/{results['total']} successful")
        
        return results


class BillingCycleManager:
    """
    Manage billing cycles using Shopify's bulk operations
    Based on: https://shopify.dev/docs/apps/build/purchase-options/subscriptions/billing-cycles/manage-in-bulk
    """
    
    def __init__(self):
        from shopify_integration.enhanced_client import EnhancedShopifyAPIClient
        self.client = EnhancedShopifyAPIClient()
    
    def bulk_charge_subscriptions(self, start_date, end_date):
        """
        Use Shopify's bulk billing API to charge multiple subscriptions at once
        
        More efficient than individual billing attempts for large scale
        
        Args:
            start_date: Start of date range (ISO format)
            end_date: End of date range (ISO format)
            
        Returns:
            Job ID for tracking bulk operation
        """
        mutation = """
        mutation subscriptionBillingCycleBulkCharge(
          $billingAttemptExpectedDateRange: SubscriptionBillingAttemptExpectedDateRangeInput!
          $filters: SubscriptionBillingCycleBulkChargeFilterInput
        ) {
          subscriptionBillingCycleBulkCharge(
            billingAttemptExpectedDateRange: $billingAttemptExpectedDateRange
            filters: $filters
          ) {
            job {
              id
            }
            userErrors {
              message
              field
            }
          }
        }
        """
        
        variables = {
            "billingAttemptExpectedDateRange": {
                "startDate": start_date,
                "endDate": end_date
            },
            "filters": {
                "contractStatus": ["ACTIVE"],
                "billingCycleStatus": ["UNBILLED"],
                "billingAttemptStatus": "NO_ATTEMPT"
            }
        }
        
        try:
            result = self.client.execute_graphql_query(mutation, variables)
            
            if "errors" in result:
                logger.error(f"Bulk charge errors: {result['errors']}")
                return None
            
            data = result.get("data", {}).get("subscriptionBillingCycleBulkCharge", {})
            user_errors = data.get("userErrors", [])
            
            if user_errors:
                logger.error(f"Bulk charge validation errors: {user_errors}")
                return None
            
            job = data.get("job", {})
            job_id = job.get("id")
            
            logger.info(f"✅ Bulk charge job created: {job_id}")
            
            return {
                "success": True,
                "job_id": job_id,
                "start_date": start_date,
                "end_date": end_date
            }
            
        except Exception as e:
            logger.error(f"Exception in bulk charge: {e}")
            return None
    
    def get_bulk_charge_results(self, job_id):
        """
        Get results of bulk billing operation
        
        Args:
            job_id: Job ID from bulk_charge_subscriptions
            
        Returns:
            List of billing cycle results
        """
        query = """
        query getBulkResults($jobId: ID!, $first: Int!) {
          subscriptionBillingCycleBulkResults(
            jobId: $jobId
            first: $first
          ) {
            edges {
              node {
                status
                cycleIndex
                cycleStartAt
                cycleEndAt
                billingAttempts(first: 5) {
                  edges {
                    node {
                      id
                      order {
                        id
                        name
                      }
                      errorMessage
                      errorCode
                    }
                  }
                }
                sourceContract {
                  id
                  status
                  customer {
                    id
                    email
                  }
                }
              }
            }
          }
        }
        """
        
        variables = {
            "jobId": job_id,
            "first": 100  # Adjust based on scale
        }
        
        try:
            result = self.client.execute_graphql_query(query, variables)
            
            if "errors" in result:
                logger.error(f"Error fetching bulk results: {result['errors']}")
                return None
            
            data = result.get("data", {}).get("subscriptionBillingCycleBulkResults", {})
            edges = data.get("edges", [])
            
            cycles = []
            for edge in edges:
                node = edge.get("node", {})
                cycles.append({
                    'status': node.get('status'),
                    'cycle_index': node.get('cycleIndex'),
                    'contract_id': node.get('sourceContract', {}).get('id'),
                    'customer_email': node.get('sourceContract', {}).get('customer', {}).get('email'),
                    'billing_attempts': node.get('billingAttempts', {}).get('edges', [])
                })
            
            logger.info(f"✅ Retrieved {len(cycles)} billing cycle results")
            
            return cycles
            
        except Exception as e:
            logger.error(f"Exception fetching bulk results: {e}")
            return None


# Convenience functions for manual use or cron jobs

def bill_subscriptions_daily(dry_run=False):
    """
    Main function for daily billing
    
    Usage in cron:
        0 2 * * * cd /path/to/project && python manage.py shell -c "from customer_subscriptions.tasks import bill_subscriptions_daily; bill_subscriptions_daily()"
    
    Or use with Celery:
        @periodic_task(run_every=crontab(hour=2, minute=0))
        def daily_billing():
            from customer_subscriptions.tasks import bill_subscriptions_daily
            bill_subscriptions_daily()
    """
    automation = SubscriptionBillingAutomation()
    results = automation.bill_due_subscriptions(dry_run=dry_run)
    
    # Log results
    logger.info(f"Daily billing complete: {results['successful']}/{results['total']} successful")
    
    if results['failed'] > 0:
        logger.error(f"Failed billings: {results['failed']}")
        # TODO: Send admin notification
    
    return results


def retry_failed_subscriptions():
    """
    Retry subscriptions with failed billing attempts
    
    Run this daily after main billing, or on-demand
    """
    automation = SubscriptionBillingAutomation()
    results = automation.retry_failed_billings()
    
    logger.info(f"Retry complete: {results['successful']}/{results['total']} successful")
    
    return results


def bulk_bill_subscriptions(start_date=None, end_date=None):
    """
    Use Shopify's bulk billing API for high-volume billing
    
    More efficient than individual billing attempts
    Recommended for stores with 100+ subscriptions
    
    Args:
        start_date: Start date (defaults to today)
        end_date: End date (defaults to tomorrow)
    """
    if not start_date:
        start_date = date.today().isoformat() + "T00:00:00Z"
    if not end_date:
        end_date = (date.today() + timedelta(days=1)).isoformat() + "T00:00:00Z"
    
    manager = BillingCycleManager()
    
    logger.info(f"📊 Starting bulk billing for {start_date} to {end_date}")
    
    # Create bulk charge job
    result = manager.bulk_charge_subscriptions(start_date, end_date)
    
    if not result:
        logger.error("❌ Bulk charge failed")
        return None
    
    job_id = result.get('job_id')
    
    logger.info(f"⏳ Bulk charge job created: {job_id}")
    logger.info(f"   Check results in a few minutes with: get_bulk_charge_results('{job_id}')")
    
    return result


def get_bulk_charge_results(job_id):
    """
    Get results of bulk billing operation
    
    Args:
        job_id: Job ID from bulk_bill_subscriptions
    """
    manager = BillingCycleManager()
    cycles = manager.get_bulk_charge_results(job_id)
    
    if not cycles:
        logger.warning("No results yet or job failed")
        return None
    
    logger.info(f"📊 Bulk billing results:")
    
    billed = 0
    failed = 0
    
    for cycle in cycles:
        if cycle['status'] == 'BILLED':
            billed += 1
        else:
            failed += 1
        
        logger.info(f"  Contract: {cycle['contract_id']}")
        logger.info(f"  Customer: {cycle['customer_email']}")
        logger.info(f"  Status: {cycle['status']}")
        logger.info(f"  Cycle: {cycle['cycle_index']}")
    
    logger.info(f"\n✅ Total: {len(cycles)} | Billed: {billed} | Failed: {failed}")
    
    return cycles


# Example usage:
"""
# Manual testing:
python manage.py shell

>>> from customer_subscriptions.tasks import bill_subscriptions_daily
>>> bill_subscriptions_daily(dry_run=True)  # Test without actually billing
>>> bill_subscriptions_daily(dry_run=False)  # Actually bill

# Cron job (add to crontab):
0 2 * * * cd /path/to/lavish_backend && /path/to/python manage.py shell -c "from customer_subscriptions.tasks import bill_subscriptions_daily; bill_subscriptions_daily()"

# Celery (if installed):
from celery.schedules import crontab
from celery.task import periodic_task

@periodic_task(run_every=crontab(hour=2, minute=0))
def daily_subscription_billing():
    from customer_subscriptions.tasks import bill_subscriptions_daily
    return bill_subscriptions_daily()

# Django-Q (if installed):
from django_q.tasks import schedule
from django_q.models import Schedule

schedule('customer_subscriptions.tasks.bill_subscriptions_daily',
         schedule_type=Schedule.DAILY,
         next_run=datetime(2025, 12, 7, 2, 0))  # Run at 2 AM daily
"""

