"""
Email notification services for subscription management
"""
import logging
from django.template import Template, Context
from django.utils import timezone
from email_manager.models import EmailTemplate, EmailConfiguration, EmailHistory
from email_manager.utils import send_email
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SubscriptionEmailService:
    """Service for sending subscription-related emails"""
    
    @staticmethod
    def send_skip_notification(subscription, skip_month, recipient_email=None):
        """
        Send skip notification email to customer
        
        Args:
            subscription: CustomerSubscription instance
            skip_month: str - Month name (e.g., "January 2025")
            recipient_email: str - Override recipient (default: subscription customer email)
        
        Returns:
            bool: True if email sent successfully
        """
        try:
            # Get template
            template = EmailTemplate.objects.get(name='subscription_skip_notification')
            
            # Get recipient
            if not recipient_email:
                recipient_email = subscription.customer.email
            
            # Calculate skip info
            skip_obj = subscription.skips.filter(
                skip_month=skip_month.split()[0]
            ).first()
            
            skips_remaining = subscription.get_remaining_skips()
            next_skip_reset = subscription.get_next_skip_reset_date()
            unskip_deadline = None
            
            if skip_obj:
                # Deadline is typically 7 days before delivery
                delivery_date = subscription.next_delivery_date
                if delivery_date:
                    unskip_deadline = delivery_date - timedelta(days=7)
            
            # Prepare context
            context = {
                'customer_name': subscription.customer.first_name or subscription.customer.email.split('@')[0],
                'subscription_name': subscription.selling_plan.name if subscription.selling_plan else 'Subscription',
                'month_name': skip_month,
                'next_delivery_date': subscription.next_delivery_date.strftime('%B %d, %Y') if subscription.next_delivery_date else 'TBD',
                'skips_remaining': skips_remaining,
                'skip_reset_date': next_skip_reset.strftime('%B %d, %Y') if next_skip_reset else 'TBD',
                'unskip_deadline': unskip_deadline.strftime('%B %d, %Y') if unskip_deadline else None,
                'dashboard_url': f'https://7fa66c-ac.myshopify.com/account',
            }
            
            # Render template
            html_template = Template(template.html_content)
            plain_template = Template(template.plain_text_content)
            subject_template = Template(template.subject)
            
            html_content = html_template.render(Context(context))
            plain_content = plain_template.render(Context(context))
            subject = subject_template.render(Context(context))
            
            # Get email config
            config = template.configuration or EmailConfiguration.get_default()
            
            # Send email
            success = send_email(
                subject=subject,
                message=plain_content,
                from_email=config.default_from_email,
                recipient_list=[recipient_email],
                html_message=html_content,
                email_type='subscription_skip',
                related_object=subscription,
                config=config
            )
            
            if success:
                logger.info(f'Skip notification sent to {recipient_email} for subscription {subscription.id}')
            
            return success
            
        except EmailTemplate.DoesNotExist:
            logger.error('Skip notification template not found')
            return False
        except Exception as e:
            logger.error(f'Error sending skip notification: {e}')
            return False
    
    @staticmethod
    def send_address_change_notification(subscription, old_address, new_address, recipient_email=None):
        """
        Send address change notification email to customer
        
        Args:
            subscription: CustomerSubscription instance
            old_address: str - Old address text
            new_address: str - New address text
            recipient_email: str - Override recipient (default: subscription customer email)
        
        Returns:
            bool: True if email sent successfully
        """
        try:
            # Get template
            template = EmailTemplate.objects.get(name='subscription_address_change_notification')
            
            # Get recipient
            if not recipient_email:
                recipient_email = subscription.customer.email
            
            # Count affected orders
            from orders.models import ShopifyOrder
            affected_orders = ShopifyOrder.objects.filter(
                customer=subscription.customer,
                fulfillment_status__in=['unfulfilled', 'partial'],
                created_at__gte=timezone.now() - timedelta(days=30)
            ).count()
            
            # Prepare context
            context = {
                'customer_name': subscription.customer.first_name or subscription.customer.email.split('@')[0],
                'subscription_name': subscription.selling_plan.name if subscription.selling_plan else 'Subscription',
                'old_address': old_address,
                'new_address': new_address,
                'next_delivery_date': subscription.next_delivery_date.strftime('%B %d, %Y') if subscription.next_delivery_date else 'TBD',
                'change_date': timezone.now().strftime('%B %d, %Y'),
                'affected_orders_count': affected_orders,
                'dashboard_url': f'https://7fa66c-ac.myshopify.com/account',
            }
            
            # Render template
            html_template = Template(template.html_content)
            plain_template = Template(template.plain_text_content)
            subject_template = Template(template.subject)
            
            html_content = html_template.render(Context(context))
            plain_content = plain_template.render(Context(context))
            subject = subject_template.render(Context(context))
            
            # Get email config
            config = template.configuration or EmailConfiguration.get_default()
            
            # Send email
            success = send_email(
                subject=subject,
                message=plain_content,
                from_email=config.default_from_email,
                recipient_list=[recipient_email],
                html_message=html_content,
                email_type='subscription_address_change',
                related_object=subscription,
                config=config
            )
            
            if success:
                logger.info(f'Address change notification sent to {recipient_email} for subscription {subscription.id}')
            
            return success
            
        except EmailTemplate.DoesNotExist:
            logger.error('Address change notification template not found')
            return False
        except Exception as e:
            logger.error(f'Error sending address change notification: {e}')
            return False
    
    @staticmethod
    def send_renewal_reminder(subscription, recipient_email=None):
        """
        Send renewal reminder email to customer
        
        Args:
            subscription: CustomerSubscription instance
            recipient_email: str - Override recipient (default: subscription customer email)
        
        Returns:
            bool: True if email sent successfully
        """
        try:
            # Get template
            template = EmailTemplate.objects.get(name='subscription_renewal_reminder')
            
            # Get recipient
            if not recipient_email:
                recipient_email = subscription.customer.email
            
            # Calculate costs
            subscription_cost = float(subscription.total_price)
            shipping_cost = 5.00  # Default shipping
            total_cost = subscription_cost + shipping_cost
            
            # Format address
            addr = subscription.delivery_address
            delivery_address = f"{addr.get('address1', '')}, {addr.get('city', '')}, {addr.get('province', '')} {addr.get('zip', '')}" if addr else 'Not set'
            
            # Prepare context
            context = {
                'customer_name': subscription.customer.first_name or subscription.customer.email.split('@')[0],
                'subscription_name': subscription.selling_plan.name if subscription.selling_plan else 'Subscription',
                'renewal_date': subscription.next_billing_date.strftime('%B %d, %Y') if subscription.next_billing_date else 'TBD',
                'renewal_cost': f'${subscription_cost:.2f}',
                'shipping_cost': f'${shipping_cost:.2f}',
                'total_cost': f'${total_cost:.2f}',
                'payment_method': subscription.payment_method_id or 'On file',
                'delivery_address': delivery_address,
                'dashboard_url': f'https://7fa66c-ac.myshopify.com/account',
            }
            
            # Render template
            html_template = Template(template.html_content)
            plain_template = Template(template.plain_text_content)
            subject_template = Template(template.subject)
            
            html_content = html_template.render(Context(context))
            plain_content = plain_template.render(Context(context))
            subject = subject_template.render(Context(context))
            
            # Get email config
            config = template.configuration or EmailConfiguration.get_default()
            
            # Send email
            success = send_email(
                subject=subject,
                message=plain_content,
                from_email=config.default_from_email,
                recipient_list=[recipient_email],
                html_message=html_content,
                email_type='subscription_renewal',
                related_object=subscription,
                config=config
            )
            
            if success:
                logger.info(f'Renewal reminder sent to {recipient_email} for subscription {subscription.id}')
            
            return success
            
        except EmailTemplate.DoesNotExist:
            logger.error('Renewal reminder template not found')
            return False
        except Exception as e:
            logger.error(f'Error sending renewal reminder: {e}')
            return False
    
    @staticmethod
    def send_cancellation_confirmation(subscription, feedback_reason=None, recipient_email=None):
        """
        Send cancellation confirmation email to customer
        
        Args:
            subscription: CustomerSubscription instance
            feedback_reason: str - Reason for cancellation
            recipient_email: str - Override recipient (default: subscription customer email)
        
        Returns:
            bool: True if email sent successfully
        """
        try:
            # Get template
            template = EmailTemplate.objects.get(name='subscription_cancellation_confirmation')
            
            # Get recipient
            if not recipient_email:
                recipient_email = subscription.customer.email
            
            # Prepare context
            context = {
                'customer_name': subscription.customer.first_name or subscription.customer.email.split('@')[0],
                'subscription_name': subscription.selling_plan.name if subscription.selling_plan else 'Subscription',
                'cancellation_date': timezone.now().strftime('%B %d, %Y'),
                'final_delivery_date': subscription.next_delivery_date.strftime('%B %d, %Y') if subscription.next_delivery_date else 'No pending deliveries',
                'feedback_reason': feedback_reason or 'Not provided',
                'reactivate_url': f'https://7fa66c-ac.myshopify.com/account',
            }
            
            # Render template
            html_template = Template(template.html_content)
            plain_template = Template(template.plain_text_content)
            subject_template = Template(template.subject)
            
            html_content = html_template.render(Context(context))
            plain_content = plain_template.render(Context(context))
            subject = subject_template.render(Context(context))
            
            # Get email config
            config = template.configuration or EmailConfiguration.get_default()
            
            # Send email
            success = send_email(
                subject=subject,
                message=plain_content,
                from_email=config.default_from_email,
                recipient_list=[recipient_email],
                html_message=html_content,
                email_type='subscription_cancellation',
                related_object=subscription,
                config=config
            )
            
            if success:
                logger.info(f'Cancellation confirmation sent to {recipient_email} for subscription {subscription.id}')
            
            return success
            
        except EmailTemplate.DoesNotExist:
            logger.error('Cancellation confirmation template not found')
            return False
        except Exception as e:
            logger.error(f'Error sending cancellation confirmation: {e}')
            return False
    
    @staticmethod
    def send_test_email(template_name, recipient_email):
        """
        Send a test email with sample data
        
        Args:
            template_name: str - Name of the template
            recipient_email: str - Recipient email address
        
        Returns:
            bool: True if email sent successfully
        """
        try:
            template = EmailTemplate.objects.get(name=template_name)
            
            # Use template variables as context
            context = template.variables
            
            # Render template
            html_template = Template(template.html_content)
            plain_template = Template(template.plain_text_content)
            subject_template = Template(template.subject)
            
            html_content = html_template.render(Context(context))
            plain_content = plain_template.render(Context(context))
            subject = subject_template.render(Context(context))
            
            # Get email config
            config = template.configuration or EmailConfiguration.get_default()
            
            # Send email
            success = send_email(
                subject=f'[TEST] {subject}',
                message=plain_content,
                from_email=config.default_from_email,
                recipient_list=[recipient_email],
                html_message=html_content,
                email_type='test_email',
                config=config
            )
            
            if success:
                logger.info(f'Test email sent to {recipient_email} using template {template_name}')
            
            return success
            
        except EmailTemplate.DoesNotExist:
            logger.error(f'Template {template_name} not found')
            return False
        except Exception as e:
            logger.error(f'Error sending test email: {e}')
            return False
