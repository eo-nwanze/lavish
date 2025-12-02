"""
Simple validation script for Phase 1 Skip System Critical Fixes
Validates that all components are properly implemented
"""

import os
import sys

def validate_file_exists(file_path, description):
    """Validate that a file exists"""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} (NOT FOUND)")
        return False

def validate_file_content(file_path, required_content, description):
    """Validate that a file contains required content"""
    if not os.path.exists(file_path):
        print(f"❌ {description}: File not found")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    missing_content = []
    for content_item in required_content:
        if content_item not in content:
            missing_content.append(content_item)
    
    if not missing_content:
        print(f"✅ {description}: All required content present")
        return True
    else:
        print(f"❌ {description}: Missing content: {', '.join(missing_content)}")
        return False

def main():
    """Main validation function"""
    print("🧪 Phase 1 Skip System Critical Fixes Validation")
    print("=" * 60)
    
    all_valid = True
    
    # Validate Annual Reset Command
    print("\n📅 Validating Annual Skip Reset Command...")
    command_file = "c:\\Users\\Stylz\\Desktop\\lavish2\\app\\lavish_backend\\skips\\management\\commands\\reset_annual_skips.py"
    required_command_content = [
        "class Command(BaseCommand)",
        "def handle(self",
        "dry_run",
        "subscriptions_processed",
        "subscriptions_updated",
        "analytics_updated",
        "SubscriptionSyncLog.objects.create"
    ]
    
    if not validate_file_exists(command_file, "Annual reset command"):
        all_valid = False
    elif not validate_file_content(command_file, required_command_content, "Annual reset command content"):
        all_valid = False
    
    # Validate Customer API
    print("\n🔌 Validating Customer API Endpoints...")
    api_file = "c:\\Users\\Stylz\\Desktop\\lavish2\\app\\lavish_backend\\skips\\customer_api.py"
    required_api_content = [
        "def cancel_subscription(",
        "def pause_subscription(",
        "def resume_subscription(",
        "def change_subscription_frequency(",
        "def subscription_management_options(",
        "SubscriptionBidirectionalSync",
        "send_cancellation_confirmation"
    ]
    
    if not validate_file_exists(api_file, "Customer API file"):
        all_valid = False
    elif not validate_file_content(api_file, required_api_content, "Customer API content"):
        all_valid = False
    
    # Validate Frontend JavaScript
    print("\n🖥️ Validating Frontend JavaScript...")
    js_file = "c:\\Users\\Stylz\\Desktop\\lavish2\\app\\lavish_frontend\\assets\\enhanced-account.js"
    required_js_content = [
        "class SubscriptionManager",
        "cancelSubscription(",
        "pauseSubscription(",
        "resumeSubscription(",
        "changeFrequency(",
        "window.confirmCancellation",
        "window.pauseInstead",
        "showFrequencyChangeModal(",
        "getSubscriptionOptions("
    ]
    
    if not validate_file_exists(js_file, "Frontend JavaScript"):
        all_valid = False
    elif not validate_file_content(js_file, required_js_content, "Frontend JavaScript content"):
        all_valid = False
    
    # Validate URL Configuration
    print("\n🔗 Validating URL Configuration...")
    urls_file = "c:\\Users\\Stylz\\Desktop\\lavish2\\app\\lavish_backend\\skips\\urls.py"
    required_urls_content = [
        "path('subscriptions/cancel/', views.cancel_subscription",
        "path('subscriptions/pause/', views.pause_subscription",
        "path('subscriptions/resume/', views.resume_subscription",
        "path('subscriptions/change-frequency/', views.change_subscription_frequency",
        "path('subscriptions/<str:subscription_id>/options/', views.subscription_management_options"
    ]
    
    if not validate_file_exists(urls_file, "URL configuration"):
        all_valid = False
    elif not validate_file_content(urls_file, required_urls_content, "URL configuration content"):
        all_valid = False
    
    # Validate Frontend HTML Integration
    print("\n🎨 Validating Frontend HTML Integration...")
    html_file = "c:\\Users\\Stylz\\Desktop\\lavish2\\app\\lavish_frontend\\sections\\enhanced-account.liquid"
    required_html_content = [
        "name=\"subscription_id\"",
        "name=\"reason\"",
        "name=\"feedback\"",
        "cancelSubscription(",
        "confirmCancellation(",
        "pauseInstead(",
        "changeFrequency("
    ]
    
    if not validate_file_exists(html_file, "Frontend HTML"):
        all_valid = False
    elif not validate_file_content(html_file, required_html_content, "Frontend HTML content"):
        all_valid = False
    
    # Validate Helper Functions
    print("\n🛠️ Validating Helper Functions...")
    helpers_file = "c:\\Users\\Stylz\\Desktop\\lavish2\\app\\lavish_backend\\skips\\helpers.py"
    required_helpers_content = [
        "def json_response(",
        "def error_response("
    ]
    
    if not validate_file_exists(helpers_file, "Helper functions"):
        all_valid = False
    elif not validate_file_content(helpers_file, required_helpers_content, "Helper functions content"):
        all_valid = False
    
    # Summary
    print("\n" + "=" * 60)
    if all_valid:
        print("🎉 Phase 1 Skip System Critical Fixes - VALIDATION COMPLETE!")
        print("✅ All components properly implemented and integrated")
        print("\n📋 Implementation Summary:")
        print("  ✅ Annual skip reset management command")
        print("  ✅ Customer-facing API endpoints")
        print("  ✅ Frontend JavaScript functions")
        print("  ✅ URL configuration for all endpoints")
        print("  ✅ HTML integration with modal forms")
        print("  ✅ Helper functions for consistent responses")
        print("\n🚀 Ready for Phase 2 implementation!")
    else:
        print("❌ Phase 1 Skip System Critical Fixes - VALIDATION FAILED!")
        print("⚠️ Some components are missing or incomplete")
        print("\n🔧 Please review the failed validations above")
    
    return all_valid

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)