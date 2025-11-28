@echo off
echo ========================================
echo Shopify CLI Authentication Fix
echo ========================================
echo.
echo Step 1: Clearing existing authentication...
shopify auth logout

echo.
echo Step 2: Starting fresh authentication...
echo Please complete the authentication in your browser
shopify auth login

echo.
echo Step 3: Testing connection...
shopify theme list

echo.
echo ========================================
echo Authentication Complete!
echo ========================================
pause
