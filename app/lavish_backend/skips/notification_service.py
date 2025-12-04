"""
Skip Notification Service

Integrates with email_manager app to send skip-related notifications.
Handles email sending, template rendering, and notification tracking.
"""

import logging
from django.utils import timezone
from django.template.loader import render_to_string
from .models import SkipNotification

logger = logging.getLogger(__name__)


class SkipNotificationService:
    """
    Service for sending skip notifications via email_manager app
    """
    
    @staticmethod
    def send_skip_confirmed_notification(skip, subscription):
        """
        Send notification when a skip is confirmed
        
        Args:
            skip: SubscriptionSkip instance
            subscription: CustomerSubscription instance
        
        Returns:
            bool: True if notification sent successfully
        """
        try:
            # Import here to avoid circular imports
            from email_manager.utils import send_email
            from email_manager.models import EmailConfiguration
            
            # Get customer email
            recipient_email = subscription.customer.email if hasattr(subscription, 'customer') else subscription.customer_email
            
            if not recipient_email:
                logger.error(f"No email found for subscription {subscription.id}")
                return False
            
            # Get customer name
            customer_name = "Valued Customer"
            if hasattr(subscription, 'customer'):
                if subscription.customer.first_name:
                    customer_name = f"{subscription.customer.first_name} {subscription.customer.last_name}".strip()
            
            # Prepare email content
            subject = f"Skip Confirmed: Your {subscription.subscription_name if hasattr(subscription, 'subscription_name') else 'Subscription'} Order"
            
            # Plain text message
            message = f"""
Hello {customer_name},

Your subscription skip has been confirmed!

Original Order Date: {skip.original_order_date.strftime('%B %d, %Y')}
New Order Date: {skip.new_order_date.strftime('%B %d, %Y')}

Your next delivery has been rescheduled from {skip.original_order_date.strftime('%B %d, %Y')} to {skip.new_order_date.strftime('%B %d, %Y')}.

{"A skip fee of $" + str(skip.skip_fee_charged) + " has been charged to your account." if skip.skip_fee_charged > 0 else "No fee was charged for this skip."}

Thank you for your continued subscription!

Best regards,
Lavish Library Team
            """.strip()
            
            # HTML message
            html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #6200ee; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
        .content {{ background-color: #f9f9f9; padding: 30px; border: 1px solid #ddd; }}
        .date-box {{ background-color: white; padding: 15px; margin: 20px 0; border-left: 4px solid #6200ee; }}
        .footer {{ background-color: #f1f1f1; padding: 15px; text-align: center; font-size: 12px; color: #666; border-radius: 0 0 5px 5px; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #6200ee; color: white; text-decoration: none; border-radius: 5px; margin-top: 15px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✓ Skip Confirmed</h1>
        </div>
        <div class="content">
            <p>Hello {customer_name},</p>
            
            <p>Your subscription skip has been <strong>successfully confirmed</strong>!</p>
            
            <div class="date-box">
                <p><strong>Original Order Date:</strong> {skip.original_order_date.strftime('%B %d, %Y')}</p>
                <p><strong>New Order Date:</strong> {skip.new_order_date.strftime('%B %d, %Y')}</p>
            </div>
            
            <p>Your next delivery has been rescheduled from <strong>{skip.original_order_date.strftime('%B %d, %Y')}</strong> to <strong>{skip.new_order_date.strftime('%B %d, %Y')}</strong>.</p>
            
            {"<p style='color: #6200ee;'>A skip fee of <strong>$" + str(skip.skip_fee_charged) + "</strong> has been charged to your account.</p>" if skip.skip_fee_charged > 0 else "<p style='color: #28a745;'>No fee was charged for this skip.</p>"}
            
            <p>Thank you for your continued subscription!</p>
        </div>
        <div class="footer">
            <p>Lavish Library - Your Premium Book Subscription Service</p>
            <p>If you have any questions, please contact our support team.</p>
        </div>
    </div>
</body>
</html>
            """.strip()
            
            # Get email configuration
            config = EmailConfiguration.objects.filter(is_default=True).first()
            if not config:
                logger.warning("No default email configuration found")
            
            from_email = config.default_from_email if config else None
            
            # Send email using email_manager
            success = send_email(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[recipient_email],
                html_message=html_message,
                email_type='subscription_skip',
                related_object=skip,
                config=config
            )
            
            # Create notification record
            notification = SkipNotification.objects.create(
                skip=skip,
                subscription=subscription,
                notification_type='skip_confirmed',
                channel='email',
                recipient_email=recipient_email,
                subject=subject,
                message=message,
                sent_at=timezone.now() if success else None,
                delivered=success
            )
            
            if not success:
                notification.error_message = "Failed to send email via email_manager"
                notification.save()
                logger.error(f"Failed to send skip confirmation email to {recipient_email}")
            else:
                logger.info(f"Skip confirmation email sent to {recipient_email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending skip confirmation notification: {str(e)}")
            
            # Create failed notification record
            try:
                SkipNotification.objects.create(
                    skip=skip,
                    subscription=subscription,
                    notification_type='skip_confirmed',
                    channel='email',
                    recipient_email=recipient_email if 'recipient_email' in locals() else '',
                    subject=subject if 'subject' in locals() else 'Skip Confirmed',
                    message=str(e),
                    delivered=False,
                    error_message=str(e)
                )
            except Exception as inner_e:
                logger.error(f"Failed to create notification record: {str(inner_e)}")
            
            return False
    
    @staticmethod
    def send_skip_reminder_notification(subscription, days_until_cutoff):
        """
        Send reminder notification that skip deadline is approaching
        
        Args:
            subscription: CustomerSubscription instance
            days_until_cutoff: Number of days until skip deadline
        
        Returns:
            bool: True if notification sent successfully
        """
        try:
            from email_manager.utils import send_email
            from email_manager.models import EmailConfiguration
            
            recipient_email = subscription.customer.email if hasattr(subscription, 'customer') else subscription.customer_email
            
            if not recipient_email:
                logger.error(f"No email found for subscription {subscription.id}")
                return False
            
            customer_name = "Valued Customer"
            if hasattr(subscription, 'customer'):
                if subscription.customer.first_name:
                    customer_name = f"{subscription.customer.first_name} {subscription.customer.last_name}".strip()
            
            subject = f"Reminder: Skip Your Upcoming {subscription.subscription_name if hasattr(subscription, 'subscription_name') else 'Subscription'} Order"
            
            message = f"""
Hello {customer_name},

This is a reminder that your next subscription order is scheduled for {subscription.next_order_date.strftime('%B %d, %Y')}.

If you need to skip this order, you have {days_until_cutoff} days remaining to make changes.

Need to skip? Log in to your account to manage your subscription.

Thank you!

Best regards,
Lavish Library Team
            """.strip()
            
            html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #ff9800; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
        .content {{ background-color: #f9f9f9; padding: 30px; border: 1px solid #ddd; }}
        .alert-box {{ background-color: #fff3cd; padding: 15px; margin: 20px 0; border-left: 4px solid #ff9800; }}
        .footer {{ background-color: #f1f1f1; padding: 15px; text-align: center; font-size: 12px; color: #666; border-radius: 0 0 5px 5px; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #ff9800; color: white; text-decoration: none; border-radius: 5px; margin-top: 15px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⏰ Skip Reminder</h1>
        </div>
        <div class="content">
            <p>Hello {customer_name},</p>
            
            <p>This is a friendly reminder about your upcoming subscription order.</p>
            
            <div class="alert-box">
                <p><strong>Next Order Date:</strong> {subscription.next_order_date.strftime('%B %d, %Y')}</p>
                <p><strong>Time Remaining to Skip:</strong> {days_until_cutoff} days</p>
            </div>
            
            <p>If you need to skip this order, please make changes within the next <strong>{days_until_cutoff} days</strong>.</p>
            
            <p>Log in to your account to manage your subscription and skip orders as needed.</p>
            
            <a href="#" class="button">Manage Subscription</a>
        </div>
        <div class="footer">
            <p>Lavish Library - Your Premium Book Subscription Service</p>
            <p>If you have any questions, please contact our support team.</p>
        </div>
    </div>
</body>
</html>
            """.strip()
            
            config = EmailConfiguration.objects.filter(is_default=True).first()
            from_email = config.default_from_email if config else None
            
            success = send_email(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[recipient_email],
                html_message=html_message,
                email_type='subscription_reminder',
                related_object=subscription,
                config=config
            )
            
            notification = SkipNotification.objects.create(
                subscription=subscription,
                notification_type='skip_reminder',
                channel='email',
                recipient_email=recipient_email,
                subject=subject,
                message=message,
                sent_at=timezone.now() if success else None,
                delivered=success
            )
            
            if not success:
                notification.error_message = "Failed to send email via email_manager"
                notification.save()
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending skip reminder notification: {str(e)}")
            return False
    
    @staticmethod
    def send_skip_limit_reached_notification(subscription):
        """
        Send notification when customer reaches skip limit
        
        Args:
            subscription: CustomerSubscription instance
        
        Returns:
            bool: True if notification sent successfully
        """
        try:
            from email_manager.utils import send_email
            from email_manager.models import EmailConfiguration
            
            recipient_email = subscription.customer.email if hasattr(subscription, 'customer') else subscription.customer_email
            
            if not recipient_email:
                return False
            
            customer_name = "Valued Customer"
            if hasattr(subscription, 'customer'):
                if subscription.customer.first_name:
                    customer_name = f"{subscription.customer.first_name} {subscription.customer.last_name}".strip()
            
            subject = f"Skip Limit Reached - {subscription.subscription_name if hasattr(subscription, 'subscription_name') else 'Your Subscription'}"
            
            message = f"""
Hello {customer_name},

You have reached your maximum number of skips for this period.

If you need to make changes to your subscription, please contact our support team.

Thank you for your understanding!

Best regards,
Lavish Library Team
            """.strip()
            
            html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #dc3545; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
        .content {{ background-color: #f9f9f9; padding: 30px; border: 1px solid #ddd; }}
        .footer {{ background-color: #f1f1f1; padding: 15px; text-align: center; font-size: 12px; color: #666; border-radius: 0 0 5px 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚠️ Skip Limit Reached</h1>
        </div>
        <div class="content">
            <p>Hello {customer_name},</p>
            
            <p>You have reached your <strong>maximum number of skips</strong> for this period.</p>
            
            <p>If you need to make changes to your subscription, please contact our support team.</p>
            
            <p>Thank you for your understanding!</p>
        </div>
        <div class="footer">
            <p>Lavish Library - Your Premium Book Subscription Service</p>
        </div>
    </div>
</body>
</html>
            """.strip()
            
            config = EmailConfiguration.objects.filter(is_default=True).first()
            from_email = config.default_from_email if config else None
            
            success = send_email(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[recipient_email],
                html_message=html_message,
                email_type='subscription_alert',
                related_object=subscription,
                config=config
            )
            
            notification = SkipNotification.objects.create(
                subscription=subscription,
                notification_type='skip_limit_reached',
                channel='email',
                recipient_email=recipient_email,
                subject=subject,
                message=message,
                sent_at=timezone.now() if success else None,
                delivered=success
            )
            
            if not success:
                notification.error_message = "Failed to send email via email_manager"
                notification.save()
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending skip limit notification: {str(e)}")
            return False
