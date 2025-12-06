import django
import os
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from email_manager.models import EmailTemplate

print("\n" + "=" * 80)
print("EMAIL TEMPLATE VERIFICATION")
print("=" * 80)

templates = EmailTemplate.objects.all()

for template in templates:
    print(f"\n📧 {template.name}")
    print(f"   Subject: {template.subject}")
    
    # Check logo
    logo_match = re.search(r'src="([^"]*)"[^>]*alt="Lavish Library"', template.html_content)
    if logo_match:
        print(f"   ✅ Logo: {logo_match.group(1)}")
    else:
        print(f"   ⚠️  Logo not found")
    
    # Check backgrounds
    bg_cream = template.html_content.count('#FFF6EA')
    print(f"   ✅ Cream backgrounds: {bg_cream} instances")
    
    # Check for other colors that shouldn't be there
    unwanted = template.html_content.count('#F5F0E8') + template.html_content.count('#F9F6F0')
    if unwanted > 0:
        print(f"   ⚠️  Non-standard backgrounds: {unwanted}")

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
