"""
Script to create email templates for the application.
This includes: password reset, welcome email, account activation, and login notification.
"""

import os
import sys
import django

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from email_manager.models import EmailConfiguration, EmailTemplate

def create_templates():
    # Check if we have a default configuration
    config = EmailConfiguration.objects.filter(is_default=True).first()
    
    if not config:
        print("Creating default email configuration...")
        config = EmailConfiguration.objects.create(
            name="Default Configuration",
            email_host="smtp.example.com",
            email_port=587,
            email_host_user="noreply@mycomparables.com",
            email_host_password="password",
            email_use_tls=True,
            default_from_email="noreply@mycomparables.com",
            is_default=True
        )
        print("Default configuration created. Please update the settings in the admin panel.")
    
    # Create file sharing template
    file_share, created = EmailTemplate.objects.get_or_create(
        name="file_share",
        defaults={
            "template_type": "file_share",
            "subject": "File Shared with You",
            "html_content": """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>File Shared with You</title>
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
                    
                    body {
                        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                        line-height: 1.6;
                        color: #1E293B;
                        margin: 0;
                        padding: 0;
                        background-color: #F8FAFC;
                    }
                    
                    .email-container {
                        max-width: 600px;
                        margin: 0 auto;
                        background-color: #FFFFFF;
                        border-radius: 8px;
                        overflow: hidden;
                        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                    }
                    
                    .email-header {
                        background-color: #0061FE;
                        color: white;
                        padding: 24px;
                        text-align: center;
                    }
                    
                    .header-title {
                        margin: 0;
                        font-size: 24px;
                        font-weight: 600;
                    }
                    
                    .email-content {
                        padding: 32px 24px;
                    }
                    
                    .greeting {
                        font-size: 16px;
                        margin-bottom: 16px;
                    }
                    
                    .sender-info {
                        margin-bottom: 24px;
                        font-size: 16px;
                    }
                    
                    .sender-name {
                        font-weight: 600;
                        color: #1E293B;
                    }
                    
                    .file-card {
                        background-color: #F8FAFC;
                        border: 1px solid #E2E8F0;
                        border-radius: 8px;
                        padding: 20px;
                        margin-bottom: 24px;
                        display: flex;
                        align-items: flex-start;
                    }
                    
                    .file-icon {
                        width: 48px;
                        height: 48px;
                        margin-right: 16px;
                        background-color: #EFF5FE;
                        border-radius: 6px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: #0061FE;
                        font-size: 24px;
                    }
                    
                    .file-info {
                        flex: 1;
                    }
                    
                    .file-name {
                        font-weight: 600;
                        font-size: 16px;
                        margin: 0 0 8px 0;
                        color: #0F172A;
                    }
                    
                    .file-meta {
                        font-size: 14px;
                        color: #64748B;
                        margin: 0;
                    }
                    
                    .message-container {
                        background-color: #F1F5F9;
                        border-radius: 8px;
                        padding: 16px;
                        margin-bottom: 24px;
                    }
                    
                    .message-label {
                        font-weight: 600;
                        margin: 0 0 8px 0;
                        color: #475569;
                    }
                    
                    .message-content {
                        margin: 0;
                        color: #1E293B;
                        white-space: pre-line;
                    }
                    
                    .download-button {
                        display: inline-block;
                        background-color: #0061FE;
                        color: white;
                        font-weight: 600;
                        text-decoration: none;
                        padding: 12px 24px;
                        border-radius: 4px;
                        margin-top: 16px;
                        text-align: center;
                    }
                    
                    .info-text {
                        font-size: 14px;
                        color: #64748B;
                        margin-top: 24px;
                    }
                    
                    .footer {
                        text-align: center;
                        padding: 16px 24px 32px;
                        font-size: 12px;
                        color: #64748B;
                        border-top: 1px solid #E2E8F0;
                    }
                    
                    .company-logo {
                        margin-bottom: 16px;
                        font-weight: bold;
                        color: #334155;
                        font-size: 16px;
                    }
                    
                    .file-type-badge {
                        display: inline-block;
                        background-color: #E0E7FF;
                        color: #0061FE;
                        font-size: 12px;
                        font-weight: 500;
                        padding: 4px 8px;
                        border-radius: 4px;
                        margin-top: 8px;
                    }
                    
                    .avatar {
                        width: 32px;
                        height: 32px;
                        border-radius: 50%;
                        background-color: #0061FE;
                        display: inline-flex;
                        align-items: center;
                        justify-content: center;
                        color: white;
                        font-weight: bold;
                        margin-right: 8px;
                        vertical-align: middle;
                    }
                    
                    @media only screen and (max-width: 600px) {
                        .email-container {
                            border-radius: 0;
                        }
                        
                        .email-content {
                            padding: 24px 16px;
                        }
                    }
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="email-header">
                        <h1 class="header-title">File Shared with You</h1>
                    </div>
                    <div class="email-content">
                        <p class="greeting">Hello,</p>
                        
                        <div class="sender-info">
                            <div class="avatar">{{ sender_name|slice:":1" }}</div>
                            <span class="sender-name">{{ sender_name }}</span> has shared a file with you.
                        </div>
                        
                        <div class="file-card">
                            <div class="file-icon">
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                    <polyline points="14 2 14 8 20 8"></polyline>
                                    <line x1="16" y1="13" x2="8" y2="13"></line>
                                    <line x1="16" y1="17" x2="8" y2="17"></line>
                                    <polyline points="10 9 9 9 8 9"></polyline>
                                </svg>
                            </div>
                            <div class="file-info">
                                <h3 class="file-name">{{ file_name }}</h3>
                                <div class="file-type-badge">{{ file_type }}</div>
                                <p class="file-meta">Shared on {% now "F j, Y" %}</p>
                            </div>
                        </div>
                        
                        {% if message %}
                        <div class="message-container">
                            <h4 class="message-label">Message from {{ sender_name }}:</h4>
                            <p class="message-content">{{ message }}</p>
                        </div>
                        {% endif %}
                        
                        <p class="info-text">The file has been attached to this email for your convenience.</p>
                        
                        <a href="#" class="download-button">Download File</a>
                    </div>
                    <div class="footer">
                        <div class="company-logo">EnDevOps Drive</div>
                        <p>This is an automated message from EnDevOps Drive.</p>
                        <p>If you didn't expect this file, please contact the sender.</p>
                        <p>&copy; {% now "Y" %} EnDevOps. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """,
            "plain_text_content": """
            Hello,
            
            {{ sender_name }} has shared a file with you.
            
            File Name: {{ file_name }}
            File Type: {{ file_type }}
            Shared On: {% now "F j, Y" %}
            
            {% if message %}Message from {{ sender_name }}:
            {{ message }}{% endif %}
            
            The file has been attached to this email for your convenience.
            
            This is an automated message from EnDevOps Drive.
            If you didn't expect this file, please contact the sender.
            © {% now "Y" %} EnDevOps. All rights reserved.
            """,
            "configuration": config,
            "variables": {
                "sender_name": "John Doe",
                "sender_email": "john@example.com",
                "file_name": "document.pdf",
                "file_type": "PDF",
                "message": "Here's the document we discussed."
            },
            "is_active": True
        }
    )
    
    if created:
        print("File sharing template created.")
    else:
        print("File sharing template already exists.")
    
    # Create folder sharing template
    folder_share, created = EmailTemplate.objects.get_or_create(
        name="folder_share",
        defaults={
            "template_type": "folder_share",
            "subject": "Folder Shared with You",
            "html_content": """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Folder Shared with You</title>
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
                    
                    body {
                        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                        line-height: 1.6;
                        color: #1E293B;
                        margin: 0;
                        padding: 0;
                        background-color: #F8FAFC;
                    }
                    
                    .email-container {
                        max-width: 600px;
                        margin: 0 auto;
                        background-color: #FFFFFF;
                        border-radius: 8px;
                        overflow: hidden;
                        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                    }
                    
                    .email-header {
                        background-color: #0F172A;
                        color: white;
                        padding: 24px;
                        text-align: center;
                        border-bottom: 1px solid #E2E8F0;
                    }
                    
                    .header-title {
                        margin: 0;
                        font-size: 24px;
                        font-weight: 600;
                    }
                    
                    .email-content {
                        padding: 32px 24px;
                    }
                    
                    .greeting {
                        font-size: 16px;
                        margin-bottom: 16px;
                    }
                    
                    .sender-info {
                        margin-bottom: 24px;
                    }
                    
                    .sender-name {
                        font-weight: 600;
                        color: #1E293B;
                    }
                    
                    .folder-card {
                        background-color: #F8FAFC;
                        border: 1px solid #E2E8F0;
                        border-radius: 8px;
                        padding: 20px;
                        margin-bottom: 24px;
                        display: flex;
                        align-items: flex-start;
                    }
                    
                    .folder-icon {
                        width: 48px;
                        height: 48px;
                        margin-right: 16px;
                        background-color: #FEF3C7;
                        border-radius: 6px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: #D97706;
                        font-size: 24px;
                    }
                    
                    .folder-info {
                        flex: 1;
                    }
                    
                    .folder-name {
                        font-weight: 600;
                        font-size: 16px;
                        margin: 0 0 8px 0;
                        color: #0F172A;
                    }
                    
                    .folder-meta {
                        font-size: 14px;
                        color: #64748B;
                        margin: 0;
                    }
                    
                    .message-container {
                        background-color: #F1F5F9;
                        border-radius: 8px;
                        padding: 16px;
                        margin-bottom: 24px;
                    }
                    
                    .message-label {
                        font-weight: 600;
                        margin: 0 0 8px 0;
                        color: #475569;
                    }
                    
                    .message-content {
                        margin: 0;
                        color: #1E293B;
                        white-space: pre-line;
                    }
                    
                    .info-text {
                        font-size: 14px;
                        color: #64748B;
                        margin-top: 24px;
                        margin-bottom: 24px;
                    }
                    
                    .file-list-container {
                        background-color: #F8FAFC;
                        border: 1px solid #E2E8F0;
                        border-radius: 8px;
                        padding: 16px;
                        margin-bottom: 24px;
                    }
                    
                    .file-list-title {
                        font-weight: 600;
                        margin: 0 0 12px 0;
                        color: #475569;
                        font-size: 14px;
                    }
                    
                    .file-list {
                        margin: 0;
                        padding: 0 0 0 16px;
                    }
                    
                    .file-list li {
                        margin-bottom: 8px;
                        color: #334155;
                    }
                    
                    .footer {
                        text-align: center;
                        padding: 16px 24px 32px;
                        font-size: 12px;
                        color: #64748B;
                        border-top: 1px solid #E2E8F0;
                    }
                    
                    .company-logo {
                        margin-bottom: 16px;
                        font-weight: bold;
                        color: #334155;
                        font-size: 16px;
                    }
                    
                    @media only screen and (max-width: 600px) {
                        .email-container {
                            border-radius: 0;
                        }
                        
                        .email-content {
                            padding: 24px 16px;
                        }
                    }
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="email-header">
                        <h1 class="header-title">Folder Shared with You</h1>
                    </div>
                    <div class="email-content">
                        <p class="greeting">Hello,</p>
                        
                        <div class="sender-info">
                            <span class="sender-name">{{ sender_name }}</span> has shared a folder with you.
                        </div>
                        
                        <div class="folder-card">
                            <div class="folder-icon">
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                                </svg>
                            </div>
                            <div class="folder-info">
                                <h3 class="folder-name">{{ folder_name }}</h3>
                                <p class="folder-meta">Shared by {{ sender_name }} ({{ sender_email }})</p>
                            </div>
                        </div>
                        
                        {% if message %}
                        <div class="message-container">
                            <h4 class="message-label">Message from {{ sender_name }}:</h4>
                            <p class="message-content">{{ message }}</p>
                        </div>
                        {% endif %}
                        
                        <div class="file-list-container">
                            <h4 class="file-list-title">Contents:</h4>
                            <ul class="file-list">
                                {{ file_list }}
                            </ul>
                        </div>
                        
                        <p class="info-text">The folder has been compressed and attached to this email as a ZIP file.</p>
                    </div>
                    <div class="footer">
                        <div class="company-logo">EnDevOps Drive</div>
                        <p>This is an automated message.</p>
                        <p>&copy; {% now "Y" %} EnDevOps. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """,
            "plain_text_content": """
            Hello,
            
            {{ sender_name }} has shared a folder with you.
            
            Folder Name: {{ folder_name }}
            Shared By: {{ sender_name }} ({{ sender_email }})
            
            {% if message %}Message from {{ sender_name }}:
            {{ message }}{% endif %}
            
            Contents:
            {{ file_list_plain }}
            
            The folder has been compressed and attached to this email as a ZIP file.
            
            This is an automated message.
            © {% now "Y" %} EnDevOps. All rights reserved.
            """,
            "configuration": config,
            "variables": {
                "sender_name": "John Doe",
                "sender_email": "john@example.com",
                "folder_name": "Project Documents",
                "message": "Here are the project documents we discussed.",
                "file_list": "<li>document1.pdf</li><li>image.jpg</li><li>spreadsheet.xlsx</li>",
                "file_list_plain": "- document1.pdf\n- image.jpg\n- spreadsheet.xlsx"
            },
            "is_active": True
        }
    )
    
    if created:
        print("Folder sharing template created.")
    else:
        print("Folder sharing template already exists.")
    
    # Create password reset template
    password_reset, created = EmailTemplate.objects.get_or_create(
        name="password_reset",
        defaults={
            "template_type": "custom",
            "subject": "Reset your MyComparables password",
            "html_content": """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Reset Your Password</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                    }
                    .container {
                        padding: 20px;
                        background-color: #f8f9fa;
                        border-radius: 5px;
                    }
                    .header {
                        background-color: #1a2c3d;
                        color: white;
                        padding: 20px;
                        text-align: center;
                        border-radius: 5px 5px 0 0;
                    }
                    .content {
                        padding: 20px;
                        background-color: white;
                        border-radius: 0 0 5px 5px;
                    }
                    .button {
                        display: inline-block;
                        padding: 10px 20px;
                        background-color: #4fd1c5;
                        color: white;
                        text-decoration: none;
                        border-radius: 5px;
                        margin: 20px 0;
                    }
                    .footer {
                        text-align: center;
                        margin-top: 20px;
                        font-size: 12px;
                        color: #666;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Password Reset</h1>
                    </div>
                    <div class="content">
                        <p>Hello {{ username }},</p>
                        <p>You're receiving this email because you requested a password reset for your MyComparables account.</p>
                        <p>Please click the button below to choose a new password:</p>
                        <p style="text-align: center;">
                            <a href="{{ reset_url }}" class="button">Reset Password</a>
                        </p>
                        <p>Alternatively, you can copy and paste the following link in your browser:</p>
                        <p style="word-break: break-all;">{{ reset_url }}</p>
                        <p>If you didn't request a password reset, you can safely ignore this email.</p>
                        <p>Thank you,<br>The MyComparables Team</p>
                    </div>
                    <div class="footer">
                        <p>This is an automated message, please do not reply to this email.</p>
                        <p>&copy; 2024 MyComparables. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """,
            "plain_text_content": """
            Hello {{ username }},
            
            You're receiving this email because you requested a password reset for your MyComparables account.
            
            Please click on the following link to choose a new password:
            {{ reset_url }}
            
            If you didn't request a password reset, you can safely ignore this email.
            
            Thank you,
            The MyComparables Team
            
            This is an automated message, please do not reply to this email.
            © 2024 MyComparables. All rights reserved.
            """,
            "configuration": config,
            "variables": {
                "username": "johndoe",
                "reset_url": "https://mycomparables.com/accounts/reset/token123/",
            },
            "is_active": True
        }
    )
    
    if created:
        print("Password reset template created.")
    else:
        print("Password reset template already exists.")
    
    # Create welcome email template
    welcome_email, created = EmailTemplate.objects.get_or_create(
        name="welcome_email",
        defaults={
            "template_type": "welcome",
            "subject": "Welcome to MyComparables!",
            "html_content": """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Welcome to MyComparables</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                    }
                    .container {
                        padding: 20px;
                        background-color: #f8f9fa;
                        border-radius: 5px;
                    }
                    .header {
                        background-color: #1a2c3d;
                        color: white;
                        padding: 20px;
                        text-align: center;
                        border-radius: 5px 5px 0 0;
                    }
                    .content {
                        padding: 20px;
                        background-color: white;
                        border-radius: 0 0 5px 5px;
                    }
                    .feature {
                        margin: 20px 0;
                    }
                    .feature-icon {
                        font-size: 24px;
                        color: #4fd1c5;
                        margin-right: 10px;
                    }
                    .button {
                        display: inline-block;
                        padding: 10px 20px;
                        background-color: #4fd1c5;
                        color: white;
                        text-decoration: none;
                        border-radius: 5px;
                        margin: 20px 0;
                    }
                    .footer {
                        text-align: center;
                        margin-top: 20px;
                        font-size: 12px;
                        color: #666;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Welcome to MyComparables!</h1>
                    </div>
                    <div class="content">
                        <p>Hello {{ full_name }},</p>
                        <p>Thank you for joining MyComparables! We're excited to have you on board.</p>
                        <p>With your new account, you can:</p>
                        <div class="feature">
                            <span class="feature-icon">🏠</span> Compare properties and find the best deals
                        </div>
                        <div class="feature">
                            <span class="feature-icon">📊</span> Access detailed market analytics
                        </div>
                        <div class="feature">
                            <span class="feature-icon">👥</span> Connect with other real estate professionals
                        </div>
                        <div class="feature">
                            <span class="feature-icon">📱</span> Get notified about new opportunities
                        </div>
                        <p style="text-align: center;">
                            <a href="{{ login_url }}" class="button">Get Started Now</a>
                        </p>
                        <p>If you have any questions or need assistance, please don't hesitate to contact our support team.</p>
                        <p>Best regards,<br>The MyComparables Team</p>
                    </div>
                    <div class="footer">
                        <p>This is an automated message, please do not reply to this email.</p>
                        <p>&copy; 2024 MyComparables. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """,
            "plain_text_content": """
            Hello {{ full_name }},
            
            Thank you for joining MyComparables! We're excited to have you on board.
            
            With your new account, you can:
            - Compare properties and find the best deals
            - Access detailed market analytics
            - Connect with other real estate professionals
            - Get notified about new opportunities
            
            Get started now: {{ login_url }}
            
            If you have any questions or need assistance, please don't hesitate to contact our support team.
            
            Best regards,
            The MyComparables Team
            
            This is an automated message, please do not reply to this email.
            © 2024 MyComparables. All rights reserved.
            """,
            "configuration": config,
            "variables": {
                "full_name": "John Doe",
                "login_url": "https://mycomparables.com/accounts/login/",
            },
            "is_active": True
        }
    )
    
    if created:
        print("Welcome email template created.")
    else:
        print("Welcome email template already exists.")
    
    # Create account activation template
    account_activation, created = EmailTemplate.objects.get_or_create(
        name="account_activation",
        defaults={
            "template_type": "custom",
            "subject": "Activate your MyComparables account",
            "html_content": """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Activate Your Account</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                    }
                    .container {
                        padding: 20px;
                        background-color: #f8f9fa;
                        border-radius: 5px;
                    }
                    .header {
                        background-color: #1a2c3d;
                        color: white;
                        padding: 20px;
                        text-align: center;
                        border-radius: 5px 5px 0 0;
                    }
                    .content {
                        padding: 20px;
                        background-color: white;
                        border-radius: 0 0 5px 5px;
                    }
                    .button {
                        display: inline-block;
                        padding: 10px 20px;
                        background-color: #4fd1c5;
                        color: white;
                        text-decoration: none;
                        border-radius: 5px;
                        margin: 20px 0;
                    }
                    .footer {
                        text-align: center;
                        margin-top: 20px;
                        font-size: 12px;
                        color: #666;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Activate Your Account</h1>
                    </div>
                    <div class="content">
                        <p>Hello {{ full_name }},</p>
                        <p>Thank you for registering with MyComparables! We're excited to have you join our community.</p>
                        <p>To complete your registration and activate your account, please click the button below:</p>
                        <p style="text-align: center;">
                            <a href="{{ activation_url }}" class="button">Activate Account</a>
                        </p>
                        <p>Alternatively, you can copy and paste the following link in your browser:</p>
                        <p style="word-break: break-all;">{{ activation_url }}</p>
                        <p>If you didn't create an account, you can safely ignore this email.</p>
                        <p>Thank you,<br>The MyComparables Team</p>
                    </div>
                    <div class="footer">
                        <p>This is an automated message, please do not reply to this email.</p>
                        <p>&copy; 2024 MyComparables. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """,
            "plain_text_content": """
            Hello {{ full_name }},
            
            Thank you for registering with MyComparables! We're excited to have you join our community.
            
            To complete your registration and activate your account, please click on the following link:
            {{ activation_url }}
            
            If you didn't create an account, you can safely ignore this email.
            
            Thank you,
            The MyComparables Team
            
            This is an automated message, please do not reply to this email.
            © 2024 MyComparables. All rights reserved.
            """,
            "configuration": config,
            "variables": {
                "full_name": "John Doe",
                "activation_url": "https://mycomparables.com/accounts/activate/token123/",
            },
            "is_active": True
        }
    )
    
    if created:
        print("Account activation template created.")
    else:
        print("Account activation template already exists.")
    
    # Create login notification template
    login_notification, created = EmailTemplate.objects.get_or_create(
        name="login_notification",
        defaults={
            "template_type": "custom",
            "subject": "New login to your MyComparables account",
            "html_content": """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>New Login Notification</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                    }
                    .container {
                        padding: 20px;
                        background-color: #f8f9fa;
                        border-radius: 5px;
                    }
                    .header {
                        background-color: #1a2c3d;
                        color: white;
                        padding: 20px;
                        text-align: center;
                        border-radius: 5px 5px 0 0;
                    }
                    .content {
                        padding: 20px;
                        background-color: white;
                        border-radius: 0 0 5px 5px;
                    }
                    .login-details {
                        background-color: #f8f9fa;
                        padding: 15px;
                        border-radius: 5px;
                        margin: 20px 0;
                    }
                    .button {
                        display: inline-block;
                        padding: 10px 20px;
                        background-color: #4fd1c5;
                        color: white;
                        text-decoration: none;
                        border-radius: 5px;
                        margin: 20px 0;
                    }
                    .footer {
                        text-align: center;
                        margin-top: 20px;
                        font-size: 12px;
                        color: #666;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>New Login Detected</h1>
                    </div>
                    <div class="content">
                        <p>Hello {{ username }},</p>
                        <p>We detected a new login to your MyComparables account.</p>
                        <div class="login-details">
                            <p><strong>Date & Time:</strong> {{ login_time }}</p>
                            <p><strong>Device:</strong> {{ device }}</p>
                            <p><strong>Browser:</strong> {{ browser }}</p>
                            <p><strong>Location:</strong> {{ location }}</p>
                            <p><strong>IP Address:</strong> {{ ip_address }}</p>
                        </div>
                        <p>If this was you, you can safely ignore this email.</p>
                        <p>If you don't recognize this login, please secure your account immediately:</p>
                        <p style="text-align: center;">
                            <a href="{{ reset_password_url }}" class="button">Reset Password</a>
                        </p>
                        <p>If you have any concerns, please contact our support team immediately.</p>
                        <p>Thank you,<br>The MyComparables Security Team</p>
                    </div>
                    <div class="footer">
                        <p>This is an automated message, please do not reply to this email.</p>
                        <p>&copy; 2024 MyComparables. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """,
            "plain_text_content": """
            Hello {{ username }},
            
            We detected a new login to your MyComparables account.
            
            Login Details:
            - Date & Time: {{ login_time }}
            - Device: {{ device }}
            - Browser: {{ browser }}
            - Location: {{ location }}
            - IP Address: {{ ip_address }}
            
            If this was you, you can safely ignore this email.
            
            If you don't recognize this login, please secure your account immediately by resetting your password:
            {{ reset_password_url }}
            
            If you have any concerns, please contact our support team immediately.
            
            Thank you,
            The MyComparables Security Team
            
            This is an automated message, please do not reply to this email.
            © 2024 MyComparables. All rights reserved.
            """,
            "configuration": config,
            "variables": {
                "username": "johndoe",
                "login_time": "June 15, 2024, 3:45 PM",
                "device": "Windows PC",
                "browser": "Chrome 125.0",
                "location": "New York, United States",
                "ip_address": "123.45.67.89",
                "reset_password_url": "https://mycomparables.com/accounts/password_reset/",
            },
            "is_active": True
        }
    )
    
    if created:
        print("Login notification template created.")
    else:
        print("Login notification template already exists.")
    
    # Create Subscription Confirmation Email Template
    subscription_confirmation, created = EmailTemplate.objects.get_or_create(
        name="subscription_confirmation",
        defaults={
            "template_type": "subscription",
            "subject": "Your EnDevOps Storage Subscription",
            "html_content": """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Subscription Confirmation</title>
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
                    
                    body {
                        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                        line-height: 1.6;
                        color: #1E293B;
                        margin: 0;
                        padding: 0;
                        background-color: #F8FAFC;
                    }
                    
                    .email-container {
                        max-width: 600px;
                        margin: 0 auto;
                        background-color: #FFFFFF;
                        border-radius: 8px;
                        overflow: hidden;
                        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                    }
                    
                    .email-header {
                        background-color: #0061FE;
                        color: white;
                        padding: 24px;
                        text-align: center;
                    }
                    
                    .header-title {
                        margin: 0;
                        font-size: 24px;
                        font-weight: 600;
                    }
                    
                    .email-content {
                        padding: 32px 24px;
                    }
                    
                    .greeting {
                        font-size: 16px;
                        margin-bottom: 16px;
                    }
                    
                    .subscription-details {
                        background-color: #F1F5F9;
                        border-radius: 8px;
                        padding: 20px;
                        margin-bottom: 24px;
                    }
                    
                    .subscription-title {
                        font-weight: 600;
                        margin: 0 0 16px 0;
                        color: #0F172A;
                        font-size: 18px;
                    }
                    
                    .detail-row {
                        display: flex;
                        justify-content: space-between;
                        margin-bottom: 12px;
                        font-size: 14px;
                    }
                    
                    .detail-label {
                        color: #64748B;
                    }
                    
                    .detail-value {
                        font-weight: 500;
                        color: #0F172A;
                    }
                    
                    .divider {
                        height: 1px;
                        background-color: #E2E8F0;
                        margin: 16px 0;
                    }
                    
                    .total-row {
                        display: flex;
                        justify-content: space-between;
                        font-weight: 600;
                        color: #0F172A;
                        font-size: 16px;
                    }
                    
                    .info-text {
                        font-size: 14px;
                        color: #64748B;
                        margin-top: 24px;
                    }
                    
                    .cta-button {
                        display: inline-block;
                        background-color: #0061FE;
                        color: white;
                        font-weight: 600;
                        text-decoration: none;
                        padding: 12px 24px;
                        border-radius: 4px;
                        margin-top: 24px;
                        text-align: center;
                    }
                    
                    .footer {
                        text-align: center;
                        padding: 24px;
                        font-size: 12px;
                        color: #64748B;
                        border-top: 1px solid #E2E8F0;
                    }
                    
                    .company-logo {
                        margin-bottom: 16px;
                        font-weight: bold;
                        color: #334155;
                        font-size: 16px;
                    }
                    
                    @media only screen and (max-width: 600px) {
                        .email-container {
                            border-radius: 0;
                        }
                        
                        .email-content {
                            padding: 24px 16px;
                        }
                    }
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="email-header">
                        <h1 class="header-title">Subscription Confirmed</h1>
                    </div>
                    <div class="email-content">
                        <p class="greeting">Thank you for subscribing to EnDevOps Storage!</p>
                        
                        <div class="subscription-details">
                            <h2 class="subscription-title">{{ plan_name }} Plan Details</h2>
                            
                            <div class="detail-row">
                                <span class="detail-label">Plan</span>
                                <span class="detail-value">{{ plan_name }}</span>
                            </div>
                            
                            <div class="detail-row">
                                <span class="detail-label">Storage</span>
                                <span class="detail-value">{{ storage_limit }}</span>
                            </div>
                            
                            <div class="detail-row">
                                <span class="detail-label">Billing Cycle</span>
                                <span class="detail-value">{{ billing_cycle|title }}</span>
                            </div>
                            
                            <div class="divider"></div>
                            
                            <div class="total-row">
                                <span>Total</span>
                                <span>${{ amount }} / {% if billing_cycle == 'monthly' %}month{% else %}year{% endif %}</span>
                            </div>
                        </div>
                        
                        <p>Your subscription is now active and will renew automatically on {{ next_billing_date }}.</p>
                        
                        <p>You can now enjoy increased storage space and additional features. If you have any questions about your subscription, please contact our support team.</p>
                        
                        <a href="#" class="cta-button">Manage Your Storage</a>
                        
                        <p class="info-text">You can manage or cancel your subscription at any time through your account settings.</p>
                    </div>
                    <div class="footer">
                        <div class="company-logo">EnDevOps</div>
                        <p>This is an automated message from the EnDevOps system.</p>
                        <p>&copy; {% now "Y" %} EnDevOps. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """,
            "plain_text_content": """
            Thank you for subscribing to EnDevOps Storage!
            
            {{ plan_name }} Plan Details:
            
            Plan: {{ plan_name }}
            Storage: {{ storage_limit }}
            Billing Cycle: {{ billing_cycle|title }}
            
            Total: ${{ amount }} / {% if billing_cycle == 'monthly' %}month{% else %}year{% endif %}
            
            Your subscription is now active and will renew automatically on {{ next_billing_date }}.
            
            You can now enjoy increased storage space and additional features. If you have any questions about your subscription, please contact our support team.
            
            You can manage or cancel your subscription at any time through your account settings.
            
            This is an automated message from the EnDevOps system.
            © {% now "Y" %} EnDevOps. All rights reserved.
            """,
            "configuration": config,
            "variables": {
                "plan_name": "Pro",
                "storage_limit": "100GB",
                "billing_cycle": "monthly",
                "amount": "9.99",
                "next_billing_date": "2023-06-01",
            },
            "is_active": True,
        }
    )

    if created:
        print(f"Created subscription_confirmation email template")
    else:
        print(f"Email template subscription_confirmation already exists")

    # Create Subscription Canceled Email Template
    subscription_canceled, created = EmailTemplate.objects.get_or_create(
        name="subscription_canceled",
        defaults={
            "template_type": "subscription",
            "subject": "Your EnDevOps Storage Subscription Has Been Canceled",
            "html_content": """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Subscription Canceled</title>
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
                    
                    body {
                        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                        line-height: 1.6;
                        color: #1E293B;
                        margin: 0;
                        padding: 0;
                        background-color: #F8FAFC;
                    }
                    
                    .email-container {
                        max-width: 600px;
                        margin: 0 auto;
                        background-color: #FFFFFF;
                        border-radius: 8px;
                        overflow: hidden;
                        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                    }
                    
                    .email-header {
                        background-color: #64748B;
                        color: white;
                        padding: 24px;
                        text-align: center;
                    }
                    
                    .header-title {
                        margin: 0;
                        font-size: 24px;
                        font-weight: 600;
                    }
                    
                    .email-content {
                        padding: 32px 24px;
                    }
                    
                    .greeting {
                        font-size: 16px;
                        margin-bottom: 16px;
                    }
                    
                    .message-box {
                        background-color: #F1F5F9;
                        border-radius: 8px;
                        padding: 20px;
                        margin-bottom: 24px;
                    }
                    
                    .message-title {
                        font-weight: 600;
                        margin: 0 0 16px 0;
                        color: #0F172A;
                        font-size: 18px;
                    }
                    
                    .info-text {
                        font-size: 14px;
                        color: #64748B;
                        margin-top: 24px;
                    }
                    
                    .cta-button {
                        display: inline-block;
                        background-color: #0061FE;
                        color: white;
                        font-weight: 600;
                        text-decoration: none;
                        padding: 12px 24px;
                        border-radius: 4px;
                        margin-top: 24px;
                        text-align: center;
                    }
                    
                    .footer {
                        text-align: center;
                        padding: 24px;
                        font-size: 12px;
                        color: #64748B;
                        border-top: 1px solid #E2E8F0;
                    }
                    
                    .company-logo {
                        margin-bottom: 16px;
                        font-weight: bold;
                        color: #334155;
                        font-size: 16px;
                    }
                    
                    @media only screen and (max-width: 600px) {
                        .email-container {
                            border-radius: 0;
                        }
                        
                        .email-content {
                            padding: 24px 16px;
                        }
                    }
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="email-header">
                        <h1 class="header-title">Subscription Canceled</h1>
                    </div>
                    <div class="email-content">
                        <p class="greeting">We're sorry to see you go!</p>
                        
                        <div class="message-box">
                            <h2 class="message-title">Your subscription has been canceled</h2>
                            <p>Your {{ previous_plan }} plan subscription has been canceled and your account has been downgraded to the Basic plan with {{ basic_plan_limit }} of storage.</p>
                            <p>You will no longer be charged for the subscription.</p>
                        </div>
                        
                        <p>We hope you enjoyed using EnDevOps Storage. If you encountered any issues or have feedback that could help us improve our service, we'd love to hear from you.</p>
                        
                        <p>You can resubscribe at any time to regain access to premium features and increased storage.</p>
                        
                        <a href="#" class="cta-button">Resubscribe Now</a>
                        
                        <p class="info-text">If you believe this cancellation was made in error, please contact our support team immediately.</p>
                    </div>
                    <div class="footer">
                        <div class="company-logo">EnDevOps</div>
                        <p>This is an automated message from the EnDevOps system.</p>
                        <p>&copy; {% now "Y" %} EnDevOps. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """,
            "plain_text_content": """
            We're sorry to see you go!
            
            Your subscription has been canceled
            
            Your {{ previous_plan }} plan subscription has been canceled and your account has been downgraded to the Basic plan with {{ basic_plan_limit }} of storage.
            
            You will no longer be charged for the subscription.
            
            We hope you enjoyed using EnDevOps Storage. If you encountered any issues or have feedback that could help us improve our service, we'd love to hear from you.
            
            You can resubscribe at any time to regain access to premium features and increased storage.
            
            If you believe this cancellation was made in error, please contact our support team immediately.
            
            This is an automated message from the EnDevOps system.
            © {% now "Y" %} EnDevOps. All rights reserved.
            """,
            "configuration": config,
            "variables": {
                "previous_plan": "Pro",
                "basic_plan_limit": "10GB",
            },
            "is_active": True,
        }
    )

    if created:
        print(f"Created subscription_canceled email template")
    else:
        print(f"Email template subscription_canceled already exists")
    
    print("All email templates have been set up!")

def create_invoice_template():
    """Create email template for invoice notifications"""
    # Check if we have a default configuration
    config = EmailConfiguration.objects.filter(is_default=True).first()
    
    if not config:
        print("Creating default email configuration...")
        config = EmailConfiguration.objects.create(
            name="Default Configuration",
            email_host="smtp.example.com",
            email_port=587,
            email_host_user="noreply@endevops.com",
            email_host_password="password",
            email_use_tls=True,
            default_from_email="noreply@endevops.com",
            is_default=True
        )
        print("Default configuration created. Please update the settings in the admin panel.")
    
    # Create invoice notification template
    invoice_template, created = EmailTemplate.objects.get_or_create(
        name="invoice_notification",
        defaults={
            "template_type": "custom",
            "subject": "Invoice #{{invoice_number}} from Endevops",
            "html_content": """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Invoice #{{ invoice_number }}</title>
                <style>
                    body {
                        font-family: Arial, Helvetica, sans-serif;
                        margin: 0;
                        padding: 20px;
                        color: #333;
                        line-height: 1.5;
                    }
                    .email-container {
                        max-width: 600px;
                        margin: 0 auto;
                        border: 1px solid #ddd;
                        padding: 20px;
                    }
                    .header {
                        text-align: center;
                        margin-bottom: 20px;
                        padding-bottom: 20px;
                        border-bottom: 1px solid #ddd;
                    }
                    .footer {
                        margin-top: 30px;
                        padding-top: 20px;
                        border-top: 1px solid #ddd;
                        text-align: center;
                        font-size: 12px;
                        color: #777;
                    }
                    .button {
                        display: inline-block;
                        background-color: #4CAF50;
                        color: white;
                        padding: 12px 24px;
                        text-decoration: none;
                        border-radius: 4px;
                        font-weight: bold;
                        margin: 20px 0;
                    }
                    .invoice-details {
                        margin: 20px 0;
                    }
                    table {
                        width: 100%;
                        border-collapse: collapse;
                    }
                    th, td {
                        padding: 10px;
                        text-align: left;
                        border-bottom: 1px solid #ddd;
                    }
                    th {
                        background-color: #f8f8f8;
                    }
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="header">
                        <h1>ENDEVOPS</h1>
                        <h2>Invoice #{{ invoice_number }}</h2>
                    </div>
                    
                    <p>Dear {{ client.name }},</p>
                    
                    <p>Please find attached your invoice #{{ invoice_number }} for your recent services.</p>
                    
                    <div class="invoice-details">
                        <p><strong>Invoice Date:</strong> {{ invoice_date|date:"F d, Y" }}</p>
                        <p><strong>Total Amount:</strong> ${{ total_amount }}</p>
                    </div>
                    
                    <p>The invoice contains the following services:</p>
                    
                    <table>
                        <thead>
                            <tr>
                                <th>Service</th>
                                <th>Amount</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for service in services %}
                            <tr>
                                <td>{{ service.name }}</td>
                                <td>${{ service.amount }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                    
                    <p>Please make payment according to the details in the attached invoice.</p>
                    
                    <p>If you have any questions about this invoice, please don't hesitate to contact us.</p>
                    
                    <p>Thank you for your business!</p>
                    
                    <div class="footer">
                        <p>{{ company_name }}</p>
                        <p>{{ company_email }}</p>
                        <p>&copy; {% now "Y" %} Endevops. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """,
            "plain_text_content": """
            ENDEVOPS
            Invoice #{{ invoice_number }}
            
            Dear {{ client.name }},
            
            Please find attached your invoice #{{ invoice_number }} for your recent services.
            
            Invoice Date: {{ invoice_date|date:"F d, Y" }}
            Total Amount: ${{ total_amount }}
            
            The invoice contains the following services:
            {% for service in services %}
            - {{ service.name }}: ${{ service.amount }}
            {% endfor %}
            
            Please make payment according to the details in the attached invoice.
            
            If you have any questions about this invoice, please don't hesitate to contact us.
            
            Thank you for your business!
            
            {{ company_name }}
            {{ company_email }}
            © {% now "Y" %} Endevops. All rights reserved.
            """,
            "configuration": config,
            "variables": {
                "invoice_number": "INV12345",
                "client": {"name": "John Doe", "email": "john@example.com"},
                "invoice_date": "2023-01-01",
                "total_amount": "150.00",
                "subtotal": "125.00",
                "services": [{"name": "Consulting Service", "amount": "150.00"}],
                "company_name": "Endevops LLC",
                "company_email": "info@endevops.com"
            },
            "is_active": True
        }
    )
    
    if created:
        print("Created invoice notification email template")
    else:
        print("Invoice notification email template already exists")

if __name__ == "__main__":
    create_templates() 