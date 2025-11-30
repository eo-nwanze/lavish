from django.urls import path
from . import views

app_name = 'email_manager'

urlpatterns = [
    # API endpoints with csrf_exempt for testing emails
    path('test-email-config/<int:config_id>/', views.test_email_config, name='test_email_config'),
    path('debug-test/<int:config_id>/', views.debug_test_email, name='debug_test_email'),
    path('test-email-page/', views.test_email_page, name='test_email_page'),
    
    # Admin-only endpoints for testing email configurations
    path('admin/email_manager/emailconfiguration/<int:config_id>/test-email/', views.test_email_config, name='admin_test_email'),
    
    # Secondary URL pattern that is more accessible
    path('test-email/<int:config_id>/', views.test_email_config, name='simple_test_email'),
    
    # Inbox and Messages
    path('inbox/', views.inbox_list, name='inbox_list'),
    path('message/<int:pk>/', views.message_detail, name='message_detail'),
    path('compose/', views.compose_message, name='compose_message'),
    path('message/<int:pk>/reply/', views.reply_message, name='reply_message'),
    path('message/<int:pk>/forward/', views.forward_message, name='forward_message'),
    path('message/<int:pk>/toggle-favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('message/<int:pk>/add-label/', views.add_label, name='add_label'),
    path('message/<int:pk>/remove-label/', views.remove_label, name='remove_label'),
    
    # Email Guardian
    path('guardian/', views.guardian_list, name='guardian_list'),
    path('guardian/create/', views.guardian_create, name='guardian_create'),
    path('guardian/<int:pk>/edit/', views.guardian_edit, name='guardian_edit'),
    
    # Email Automation
    path('automation/', views.automation_list, name='automation_list'),
    path('automation/create/', views.automation_create, name='automation_create'),
    path('automation/<int:pk>/edit/', views.automation_edit, name='automation_edit'),
    
    # Security Alerts
    path('alerts/', views.security_alerts, name='security_alerts'),
    path('alerts/<int:pk>/resolve/', views.resolve_alert, name='resolve_alert'),
    
    # Fetch and Send Emails
    path('fetch-emails/', views.fetch_inbox_emails_view, name='fetch_inbox_emails'),
    path('message/<int:pk>/send/', views.send_email_view, name='send_email'),
] 