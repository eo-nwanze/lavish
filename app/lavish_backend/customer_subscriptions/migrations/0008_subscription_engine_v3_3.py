# Generated migration for Subscription Engine v3.3

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('customer_subscriptions', '0002_subscriptionaddress_shippingcutofflog_and_more'),
    ]

    operations = [
        # Add spot limits and waitlist fields to SellingPlan
        migrations.AddField(
            model_name='sellingplan',
            name='max_spots',
            field=models.IntegerField(null=True, blank=True, help_text='Maximum number of subscription spots available. Leave empty for unlimited.'),
        ),
        migrations.AddField(
            model_name='sellingplan',
            name='current_spots_taken',
            field=models.IntegerField(default=0, help_text='Current number of active subscriptions for this plan'),
        ),
        migrations.AddField(
            model_name='sellingplan',
            name='waitlist_enabled',
            field=models.BooleanField(default=False, help_text='Enable waitlist when spots are full'),
        ),
        migrations.AddField(
            model_name='sellingplan',
            name='waitlist_password',
            field=models.CharField(max_length=100, blank=True, help_text='Password required to see available spots'),
        ),
        migrations.AddField(
            model_name='sellingplan',
            name='unique_signup_link',
            field=models.CharField(max_length=200, blank=True, null=True, unique=True, help_text='Unique link to hide available spots from public'),
        ),
        
        # Add cancellation survey fields to CustomerSubscription
        migrations.AddField(
            model_name='customersubscription',
            name='cancellation_reason',
            field=models.CharField(
                max_length=50,
                blank=True,
                choices=[
                    ('too_expensive', 'Too expensive'),
                    ('not_using', 'Not using enough'),
                    ('quality_issues', 'Quality issues'),
                    ('found_alternative', 'Found alternative'),
                    ('moving', 'Moving/relocating'),
                    ('temporary_pause', 'Temporary pause'),
                    ('other', 'Other reason'),
                ],
                help_text='Reason for cancellation'
            ),
        ),
        migrations.AddField(
            model_name='customersubscription',
            name='cancellation_survey_data',
            field=models.JSONField(null=True, blank=True, help_text='Additional survey data from cancellation'),
        ),
        migrations.AddField(
            model_name='customersubscription',
            name='cancelled_at',
            field=models.DateTimeField(null=True, blank=True, help_text='When subscription was cancelled'),
        ),
        
        # Add renewal calendar fields
        migrations.AddField(
            model_name='customersubscription',
            name='renewal_schedule_months',
            field=models.IntegerField(default=12, help_text='Number of months to display in renewal calendar'),
        ),
        
        # Create Waitlist model
        migrations.CreateModel(
            name='SubscriptionWaitlist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254)),
                ('first_name', models.CharField(max_length=100, blank=True)),
                ('last_name', models.CharField(max_length=100, blank=True)),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('notified_at', models.DateTimeField(null=True, blank=True, help_text='When customer was notified of spot availability')),
                ('converted_at', models.DateTimeField(null=True, blank=True, help_text='When customer converted to active subscription')),
                ('status', models.CharField(
                    max_length=20,
                    choices=[
                        ('waiting', 'Waiting'),
                        ('notified', 'Notified'),
                        ('converted', 'Converted'),
                        ('expired', 'Expired'),
                    ],
                    default='waiting'
                )),
                ('selling_plan', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='waitlist_entries',
                    to='customer_subscriptions.sellingplan'
                )),
            ],
            options={
                'ordering': ['joined_at'],
                'verbose_name': 'Subscription Waitlist Entry',
                'verbose_name_plural': 'Subscription Waitlist Entries',
            },
        ),
        
        # Add unique constraint for waitlist
        migrations.AddConstraint(
            model_name='subscriptionwaitlist',
            constraint=models.UniqueConstraint(
                fields=['email', 'selling_plan'],
                name='unique_email_per_selling_plan'
            ),
        ),
    ]
