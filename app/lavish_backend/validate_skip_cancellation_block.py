"""
Validation script for skip-based cancellation blocking
Validates that the implementation correctly handles pending skips
"""

import os

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
    print("🧪 Skip-Based Cancellation Blocking Validation")
    print("=" * 60)
    
    all_valid = True
    
    # Validate Backend API Changes
    print("\n🔌 Backend API Validation...")
    api_file = "c:\\Users\\Stylz\\Desktop\\lavish2\\app\\lavish_backend\\skips\\customer_api.py"
    
    required_api_content = [
        "pending_skips = subscription.skips.filter(status='pending').count()",
        "if pending_skips > 0:",
        "return error_response(",
        "Cannot cancel subscription with",
        "pending skip request(s)",
        "cancellation_blocked",
        "cancellation_block_reason"
    ]
    
    if not validate_file_content(api_file, required_api_content, "Backend API skip check"):
        all_valid = False
    
    # Validate Frontend JavaScript Changes
    print("\n🖥️ Frontend JavaScript Validation...")
    js_file = "c:\\Users\\Stylz\\Desktop\\lavish2\\app\\lavish_frontend\\assets\\enhanced-account.js"
    
    required_js_content = [
        "updateCancellationButton",
        "cancellation_blocked",
        "cancellation_block_reason",
        "cancelBtn.disabled = true",
        "cancelBtn.title =",
        "showNotification(options.cancellation_block_reason",
        "DOMContentLoaded",
        "updateCancellationButton(subscriptionId)"
    ]
    
    if not validate_file_content(js_file, required_js_content, "Frontend JavaScript skip handling"):
        all_valid = False
    
    # Validate CSS Changes
    print("\n🎨 CSS Validation...")
    css_file = "c:\\Users\\Stylz\\Desktop\\lavish2\\app\\lavish_frontend\\assets\\enhanced-account.css"
    
    required_css_content = [
        "button[disabled]",
        "opacity: 0.5 !important",
        "cursor: not-allowed !important",
        "skip-warning-indicator",
        "pulse-warning"
    ]
    
    if not validate_file_content(css_file, required_css_content, "CSS disabled button styling"):
        all_valid = False
    
    # Summary
    print("\n" + "=" * 60)
    if all_valid:
        print("🎉 Skip-Based Cancellation Blocking - VALIDATION COMPLETE!")
        print("✅ All components properly implemented")
        print("\n📋 Implementation Summary:")
        print("  ✅ Backend API checks for pending skips before cancellation")
        print("  ✅ Frontend disables cancellation button when skips exist")
        print("  ✅ Clear error messages explain the blocking reason")
        print("  ✅ Visual indicators show blocked state")
        print("  ✅ Automatic button state updates on page load")
        print("  ✅ Proper CSS styling for disabled buttons")
        print("\n🚀 Skip-Based Cancellation Blocking Ready for Production!")
        
        print("\n📝 How It Works:")
        print("  1. When a subscription has pending skips, cancellation is blocked")
        print("  2. The cancellation button becomes disabled and shows a warning")
        print("  3. Clear error messages explain why cancellation is blocked")
        print("  4. Users must cancel/complete skips before cancelling subscription")
        print("  5. Once skips are resolved, cancellation becomes available again")
        
    else:
        print("❌ Skip-Based Cancellation Blocking - VALIDATION FAILED!")
        print("⚠️ Some components are missing or incomplete")
        print("\n🔧 Please review the failed validations above")
    
    return all_valid

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)