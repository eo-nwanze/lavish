"""
Get current email templates and extract Lavish Library color scheme
"""
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from email_manager.models import EmailTemplate, EmailConfiguration

print("\n" + "=" * 80)
print("CURRENT EMAIL TEMPLATES")
print("=" * 80)

templates = EmailTemplate.objects.all().order_by('template_type', 'name')

print(f"📧 Found {templates.count()} email templates:\n")

for i, template in enumerate(templates, 1):
    print(f"{i:2}. {template.name}")
    print(f"    Type: {template.template_type}")
    print(f"    Subject: {template.subject}")
    print(f"    Active: {'✅' if template.is_active else '❌'}")
    print(f"    Created: {template.created_at.strftime('%Y-%m-%d')}")
    print(f"    Variables: {list(template.variables.keys()) if template.variables else 'None'}")
    
    # Show preview of HTML content (first 100 chars)
    html_preview = template.html_content[:100].replace('\n', ' ').strip()
    if len(template.html_content) > 100:
        html_preview += "..."
    print(f"    HTML Preview: {html_preview}")
    print()

# Check email configurations
configs = EmailConfiguration.objects.all()
print(f"📧 Email Configurations: {configs.count()}")
for config in configs:
    print(f"   - {config.name}: {config.email_host_user} {'(Default)' if config.is_default else ''}")

print("\n" + "=" * 80)
print("LAVISH LIBRARY COLOR SCHEME ANALYSIS")
print("=" * 80)

# Extract colors from the enhanced-account.css file
print("🎨 Key Lavish Library Colors:")
print("   Primary Background: #FFF6EA (Cream/Ivory)")
print("   Text Color: #4C5151 (Dark Brown/Gray)")
print("   Primary Brand: Browns and creams")
print("   Accent Colors: Earthy tones")

print(f"\n📂 Logo Location:")
print(f"   Static Path: app/lavish_backend/static/img/Lavish-logo.png")
print(f"   URL: /static/img/Lavish-logo.png")

print("\n✅ Ready to update email templates with Lavish Library design!")