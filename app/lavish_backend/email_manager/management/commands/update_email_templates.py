from django.core.management.base import BaseCommand
from django.utils import timezone
from email_manager.models import EmailTemplate
import re
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update all email templates with a consistent design'
    
    def handle(self, *args, **options):
        """Update all email templates with the new design"""
        self.stdout.write(self.style.SUCCESS("Updating email templates with new design..."))
        
        templates = EmailTemplate.objects.all()
        
        self.stdout.write(f"Found {templates.count()} templates to update")
        updated_count = 0
        
        for template in templates:
            try:
                new_html = self.wrap_template_content(template.html_content, template.name)
                
                # Update the template
                template.html_content = new_html
                template.updated_at = timezone.now()
                template.save()
                
                updated_count += 1
                self.stdout.write(f"Updated template: {template.name}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error updating template {template.name}: {str(e)}"))
        
        self.stdout.write(self.style.SUCCESS(f"Successfully updated {updated_count} of {templates.count()} templates"))
    
    def wrap_template_content(self, original_content, template_name):
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
            
        # Common CSS
        common_css = """
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        body {
            font-family: 'Inter', sans-serif;
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
        }
        """
            
        # Get header HTML
        header_html = """
        <div class="header">
            <img src="https://kora.com/logo.png" alt="Kora" class="logo">
        </div>
        """
        
        # Get footer HTML with current year
        current_year = timezone.now().year
        footer_html = f"""
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
        
        # Create the new template with consistent styling
        new_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{template_name}</title>
    <style>
{common_css}
    </style>
</head>
<body>
    <div class="container">
{header_html}
        <div class="content">
{body_content.strip()}
        </div>
{footer_html}
    </div>
</body>
</html>"""
        
        return new_template 