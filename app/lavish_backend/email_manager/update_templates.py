"""
Script to update all email templates with a consistent design.
This script will update all existing email templates with a new design
that features a consistent header and footer, dark blue buttons, and a clean layout.
"""

import os
import django
from django.utils import timezone

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from email_manager.models import EmailTemplate
import re

def get_common_css():
    """Return common CSS for all email templates"""
    return """
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }
        
        .container {
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        
        .header {
            background-color: #222;
            padding: 20px;
            text-align: center;
        }
        
        .logo {
            max-width: 120px;
            height: auto;
        }
        
        .content {
            padding: 30px 20px;
        }
        
        .button {
            display: inline-block;
            background-color: #00336e;
            color: white !important;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 4px;
            font-weight: 600;
            margin-top: 15px;
            text-align: center;
        }
        
        .button:hover {
            background-color: #002552;
        }
        
        .message {
            padding: 20px;
            background-color: #f9f9f9;
            border-left: 4px solid #00336e;
            margin: 20px 0;
        }
        
        .footer {
            text-align: center;
            padding: 20px;
            background-color: #f5f5f5;
            color: #666;
            font-size: 12px;
            border-top: 1px solid #eaeaea;
        }
        
        .social {
            margin: 15px 0;
        }
        
        .social a {
            color: #00336e;
            text-decoration: none;
            margin: 0 10px;
            font-weight: 500;
        }
        
        .unsubscribe {
            color: #999;
            margin-top: 10px;
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: #00336e;
        }
        
        p {
            margin-bottom: 1em;
        }
        
        .divider {
            height: 1px;
            background-color: #eaeaea;
            margin: 20px 0;
        }
    """

def get_header_html():
    """Return HTML for the common header"""
    return """
    <div class="header">
        <img src="https://kora.com/logo.png" alt="Kora" class="logo">
    </div>
    """

def get_footer_html():
    """Return HTML for the common footer"""
    current_year = timezone.now().year
    
    return f"""
    <div class="footer">
        <div class="social">
            <a href="https://facebook.com/yourcompany">Facebook</a> | 
            <a href="https://twitter.com/yourcompany">Twitter</a> | 
            <a href="https://instagram.com/yourcompany">Instagram</a> | 
            <a href="https://linkedin.com/company/yourcompany">LinkedIn</a>
        </div>
        <p>© {current_year} Kora. All rights reserved.</p>
        <p class="unsubscribe">You're receiving this email because you've subscribed to our newsletter.<br>
        <a href="{{{{ unsubscribe_url }}}}">Unsubscribe</a> if you no longer wish to receive these emails.</p>
    </div>
    """

def wrap_template_content(original_content, template_name):
    """
    Extract the body content from the original template and wrap it in the new design
    """
    # Extract the main content from the original template
    body_content = ""
    
    # Try to extract content between the body tags
    body_match = re.search(r'<body[^>]*>(.*?)<\/body>', original_content, re.DOTALL)
    
    if body_match:
        body_content = body_match.group(1)
        
        # Remove header and footer if they exist
        # This is a simple approach and might need refinement for specific templates
        body_content = re.sub(r'<div[^>]*header[^>]*>.*?<\/div>', '', body_content, flags=re.DOTALL)
        body_content = re.sub(r'<div[^>]*footer[^>]*>.*?<\/div>', '', body_content, flags=re.DOTALL)
        
        # Replace old buttons with new styled ones
        body_content = re.sub(
            r'<a\s+[^>]*class=["\'](.*?button.*?)["\'](.*?)>(.*?)<\/a>',
            r'<a class="button"\2>\3</a>',
            body_content
        )
    else:
        # If no body tag is found, use the entire content
        body_content = original_content
        
    # Create the new template with consistent styling
    new_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{template_name}</title>
    <style>
    {get_common_css()}
    </style>
</head>
<body>
    <div class="container">
        {get_header_html()}
        <div class="content">
            {body_content.strip()}
        </div>
        {get_footer_html()}
    </div>
</body>
</html>"""
    
    return new_template

def update_templates():
    """Update all email templates with the new design"""
    templates = EmailTemplate.objects.all()
    
    print(f"Found {templates.count()} templates to update")
    updated_count = 0
    
    for template in templates:
        try:
            original_html = template.html_content
            new_html = wrap_template_content(original_html, template.name)
            
            # Update the template
            template.html_content = new_html
            template.updated_at = timezone.now()
            template.save()
            
            updated_count += 1
            print(f"Updated template: {template.name}")
        except Exception as e:
            print(f"Error updating template {template.name}: {str(e)}")
    
    print(f"Successfully updated {updated_count} of {templates.count()} templates")

if __name__ == "__main__":
    update_templates() 