# Skip Notification System Integration

## Overview

The Skip Notification system is fully integrated with the Email Manager app to send professional email notifications for subscription skip events.

## Features

### 1. **Skip Confirmed Notifications**
- Automatically sent when a customer confirms a skip
- Includes original and new order dates
- Shows skip fee (if applicable)
- Professional HTML email template

### 2. **Skip Reminder Notifications**
- Reminds customers about upcoming order dates
- Configurable days before order date
- Alerts customers about remaining time to skip

### 3. **Skip Limit Reached Notifications**
- Notifies customers when they reach their skip limit
- Provides instructions to contact support

## Integration with Email Manager

All skip notifications use the `email_manager` app for:
- Email configuration management
- Email sending with retry logic
- HTML and plain text email support
- Email history tracking
- Delivery status monitoring

## Usage

### Automatic Notifications

When a skip is confirmed via the API or admin:
```python
from skips.notification_service import SkipNotificationService

# Automatically sent when skip is confirmed
skip.confirm_skip()
SkipNotificationService.send_skip_confirmed_notification(skip, subscription)
```

### Manual Notifications from Admin

1. Go to Django Admin → Skips → Subscription Skips
2. Select skip(s) to notify
3. Choose "Send email notifications" action
4. Click "Go"

### Resend Failed Notifications

1. Go to Django Admin → Skips → Skip Notifications
2. Filter by delivered=False
3. Select notification(s)
4. Choose "Resend failed notifications" action
5. Click "Go"

### Send Skip Reminders (Scheduled)

Use the management command to send reminders:

```bash
# Send reminders 7 days before order date
python manage.py send_skip_reminders

# Send reminders 14 days before order date
python manage.py send_skip_reminders --days-before 14

# Dry run (test without sending)
python manage.py send_skip_reminders --dry-run
```

## Notification Types

### 1. Skip Confirmed (`skip_confirmed`)
**Trigger**: When a skip is successfully confirmed
**Template**: Professional confirmation with date changes
**Features**:
- Original vs New order dates highlighted
- Skip fee information
- Success confirmation badge

### 2. Skip Reminder (`skip_reminder`)
**Trigger**: X days before next order date (configurable)
**Template**: Friendly reminder with urgency
**Features**:
- Days remaining countdown
- Manage subscription CTA button
- Warning-styled header

### 3. Skip Limit Reached (`skip_limit_reached`)
**Trigger**: When customer reaches maximum skips
**Template**: Alert notification
**Features**:
- Clear limit reached message
- Support contact information
- Alert-styled header

## Email Templates

All emails include:
- **Professional HTML design** with Lavish Library branding
- **Responsive layout** (mobile-friendly)
- **Plain text fallback** for email clients that don't support HTML
- **Clear call-to-action buttons**
- **Brand colors** (Purple #6200ee primary)

### Customization

To customize email templates, edit:
`skips/notification_service.py`

Look for the `html_message` and `message` variables in each notification method.

## Database Tracking

All notifications are tracked in the `SkipNotification` model:

**Fields:**
- `notification_type`: Type of notification sent
- `channel`: Delivery channel (email, sms, push)
- `recipient_email`: Email address
- `subject`: Email subject line
- `message`: Email content
- `sent_at`: Timestamp when sent
- `delivered`: Success status
- `error_message`: Error details if failed

**Admin Interface:**
- View all sent notifications
- Filter by type, status, date
- Resend failed notifications
- Mark as delivered manually

## Email Configuration

Notifications use the **default email configuration** from Email Manager.

To set up:
1. Go to Django Admin → Email Manager → Email Configurations
2. Create or edit a configuration
3. Check "Is default"
4. Configure SMTP settings:
   - Email Host (e.g., smtp.gmail.com)
   - Email Port (e.g., 587)
   - Email Host User
   - Email Host Password
   - Use TLS/SSL

## Testing

### Test Skip Confirmation Email

```python
from skips.models import SubscriptionSkip
from skips.notification_service import SkipNotificationService

# Get a skip instance
skip = SubscriptionSkip.objects.get(pk=1)

# Send notification
SkipNotificationService.send_skip_confirmed_notification(
    skip=skip,
    subscription=skip.subscription
)
```

### Test Skip Reminder

```python
from customer_subscriptions.models import CustomerSubscription
from skips.notification_service import SkipNotificationService

# Get subscription
subscription = CustomerSubscription.objects.get(pk=1)

# Send reminder
SkipNotificationService.send_skip_reminder_notification(
    subscription=subscription,
    days_until_cutoff=7
)
```

## Scheduled Tasks

Set up a cron job or task scheduler to run skip reminders:

**Example cron (runs daily at 9 AM):**
```bash
0 9 * * * cd /path/to/project && python manage.py send_skip_reminders --days-before 7
```

**Example with multiple reminder periods:**
```bash
# 7 days before
0 9 * * * cd /path/to/project && python manage.py send_skip_reminders --days-before 7

# 14 days before
0 9 * * * cd /path/to/project && python manage.py send_skip_reminders --days-before 14

# 3 days before (final reminder)
0 9 * * * cd /path/to/project && python manage.py send_skip_reminders --days-before 3
```

## Error Handling

The notification service includes comprehensive error handling:

1. **Email Configuration Missing**: Logs warning and attempts to send anyway
2. **Invalid Email Address**: Logs error and records failed notification
3. **SMTP Connection Failure**: Retries with email_manager retry logic
4. **Template Rendering Errors**: Logs error and creates failed notification record

All errors are:
- Logged to Django logs
- Recorded in SkipNotification model
- Visible in Django Admin
- Can be retried manually

## API Integration

Skip notifications are automatically triggered by the skip creation API:

**POST** `/api/skips/`

```json
{
  "subscription_id": 123,
  "skip_date": "2025-12-15",
  "reason": "Going on vacation"
}
```

Response includes notification status:
```json
{
  "success": true,
  "message": "Skip confirmed and notification sent",
  "skip_id": 456
}
```

## Monitoring

### Check Notification Status

**Django Admin:**
- Skips → Skip Notifications
- Filter by delivered=False to see failures
- Check error_message field for details

**Database Query:**
```python
from skips.models import SkipNotification

# Failed notifications today
failed_today = SkipNotification.objects.filter(
    delivered=False,
    created_at__date=timezone.now().date()
)

# Success rate
total = SkipNotification.objects.count()
successful = SkipNotification.objects.filter(delivered=True).count()
success_rate = (successful / total * 100) if total > 0 else 0
```

## Best Practices

1. **Test email configuration** before enabling notifications
2. **Use dry-run mode** when testing reminder commands
3. **Monitor failed notifications** regularly in admin
4. **Set up multiple reminder periods** (7, 14, 3 days)
5. **Review email templates** for branding consistency
6. **Check spam filters** if customers report not receiving emails
7. **Keep email configuration secure** (use environment variables for passwords)

## Troubleshooting

### Emails Not Sending

1. Check email configuration in admin
2. Test configuration with "Test Email" button
3. Check Django logs for errors
4. Verify SMTP credentials
5. Check firewall/network settings

### Emails in Spam

1. Configure SPF/DKIM records for your domain
2. Use authenticated SMTP server
3. Avoid spam trigger words in subject/content
4. Send from legitimate domain

### Wrong Customer Information

1. Verify subscription has correct customer relationship
2. Check customer.email field is populated
3. Verify customer name fields

## Future Enhancements

- [ ] SMS notification support
- [ ] Push notification support
- [ ] Customizable email templates via admin
- [ ] Multi-language support
- [ ] A/B testing for email content
- [ ] Email open/click tracking
- [ ] Webhook support for external services

## Support

For issues or questions:
1. Check Django logs: `logs/django.log`
2. Review Email History in admin
3. Check Skip Notification records
4. Contact development team
