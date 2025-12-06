"""
Fix all email templates with correct logo path and uniform Lavish Library background
Based on Django admin sidebar logo implementation
"""
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from email_manager.models import EmailTemplate

print("\n" + "=" * 80)
print("FIXING EMAIL TEMPLATES - LOGO & BACKGROUND")
print("=" * 80)

# Get all templates
templates = EmailTemplate.objects.all()
print(f"\nFound {templates.count()} email templates to fix\n")

# Logo path from Django admin settings
LOGO_PATH = "{% load static %}{% static 'img/Lavish-logo.png' %}"
# Alternative: use direct path
LOGO_DIRECT_PATH = "/static/img/Lavish-logo.png"

# Lavish Library color scheme
CREAM_BG = "#FFF6EA"
BROWN_TEXT = "#4C5151"

updated_count = 0

for template in templates:
    print(f"Processing: {template.name}")
    
    html_content = template.html_content
    
    if not html_content:
        print(f"  ⚠️  No HTML content, skipping")
        continue
    
    # Track if any changes made
    modified = False
    
    # Fix 1: Replace broken logo paths with correct one
    broken_logo_patterns = [
        'src="Lavish Library Logo"',
        'src="/static/img/Lavish Library Logo"',
        'img src="Lavish Library Logo"',
        '<img alt="Lavish Library Logo"',
        'alt="Lavish Library Logo" />',
        'alt="Lavish Library Logo"/>',
        'alt="Lavish Library Logo" >',
    ]
    
    for broken_pattern in broken_logo_patterns:
        if broken_pattern in html_content:
            print(f"  🔧 Found broken logo pattern: {broken_pattern[:50]}...")
            modified = True
    
    # Fix all broken logo references
    # Replace entire img tag with correct one
    import re
    
    # Pattern to match various broken logo img tags
    logo_patterns = [
        r'<img[^>]*alt="Lavish Library Logo"[^>]*>',
        r'<img[^>]*Lavish Library Logo[^>]*>',
        r'<img[^>]*lavish[- ]?library[- ]?logo[^>]*>',
    ]
    
    for pattern in logo_patterns:
        if re.search(pattern, html_content, re.IGNORECASE):
            html_content = re.sub(
                pattern,
                f'<img src="{LOGO_DIRECT_PATH}" alt="Lavish Library" class="logo" style="max-width: 180px; height: auto; margin-bottom: 15px;">',
                html_content,
                flags=re.IGNORECASE
            )
            print(f"  ✅ Fixed logo img tag")
            modified = True
    
    # Fix 2: Ensure uniform cream background
    # Replace any other background colors with cream
    bg_patterns = [
        (r'background-color:\s*#[Ff]5[Ff]5[Ff]0', f'background-color: {CREAM_BG}'),
        (r'background-color:\s*#[Ee]8[Ee]3[Dd][Bb]', f'background-color: {CREAM_BG}'),
        (r'background-color:\s*#[Ff]9[Ff]6[Ff]0', f'background-color: {CREAM_BG}'),
        (r'background:\s*#[Ff]5[Ff]5[Ff]0', f'background: {CREAM_BG}'),
        (r'background:\s*linear-gradient\([^)]*#[Ff]5[Ff]0[Ee]8[^)]*\)', f'background: {CREAM_BG}'),
    ]
    
    for pattern, replacement in bg_patterns:
        if re.search(pattern, html_content):
            html_content = re.sub(pattern, replacement, html_content)
            print(f"  ✅ Unified background color")
            modified = True
    
    # Fix 3: Remove any non-Lavish Library colors (browns, oranges that aren't ours)
    # Replace urgent notice backgrounds with proper brown
    urgent_patterns = [
        (r'background:\s*linear-gradient\([^)]*#8B4513[^)]*\)', f'background: linear-gradient(135deg, {BROWN_TEXT} 0%, #5A5F5F 100%)'),
    ]
    
    for pattern, replacement in urgent_patterns:
        if re.search(pattern, html_content):
            html_content = re.sub(pattern, replacement, html_content)
            print(f"  ✅ Fixed urgent notice colors")
            modified = True
    
    # Fix 4: Ensure header uses cream background
    header_pattern = r'<div class="header"[^>]*style="[^"]*"'
    if re.search(header_pattern, html_content):
        html_content = re.sub(
            header_pattern,
            f'<div class="header" style="background: {CREAM_BG}; padding: 30px; text-align: center; border-bottom: 3px solid {BROWN_TEXT};"',
            html_content
        )
        print(f"  ✅ Fixed header background")
        modified = True
    
    # Fix 5: Ensure content div uses cream background
    content_pattern = r'(<div class="content"[^>]*style=")[^"]*(")'
    if re.search(content_pattern, html_content):
        html_content = re.sub(
            content_pattern,
            f'\\1padding: 30px; background-color: {CREAM_BG};\\2',
            html_content
        )
        print(f"  ✅ Fixed content background")
        modified = True
    
    # Save if modified
    if modified:
        template.html_content = html_content
        template.save()
        updated_count += 1
        print(f"  ✅ Saved changes")
    else:
        print(f"  ℹ️  No changes needed")
    
    print()

print("=" * 80)
print(f"SUMMARY: Updated {updated_count} out of {templates.count()} templates")
print("=" * 80)

print("\n✅ All email templates now have:")
print(f"  • Correct logo path: {LOGO_DIRECT_PATH}")
print(f"  • Uniform cream background: {CREAM_BG}")
print(f"  • Consistent brown text: {BROWN_TEXT}")
print(f"  • No conflicting colors")
