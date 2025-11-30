@echo off
echo ========================================
echo  Subscription Skip System - Quick Test
echo ========================================
echo.

cd "c:\Users\eonwa\Desktop\Lavish Library\app\lavish_backend"

echo [1/5] Activating virtual environment...
call ..\lavish_backend_env\Scripts\activate.bat
echo.

echo [2/5] Checking Django configuration...
python manage.py check
echo.

echo [3/5] Initializing skip policies and sample data...
python manage.py sync_subscriptions
echo.

echo [4/5] Starting Django development server on port 8003...
echo.
echo ========================================
echo  TEST ENDPOINTS:
echo ========================================
echo  Health Check:      http://localhost:8003/api/skips/health/
echo  Sample Sub:        http://localhost:8003/api/skips/subscriptions/gid://shopify/SubscriptionContract/SAMPLE123/
echo  Django Admin:      http://localhost:8003/admin/skips/
echo ========================================
echo.
echo Press Ctrl+C to stop the server
echo.

python manage.py runserver 8003
