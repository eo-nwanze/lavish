@echo off
echo ========================================
echo Crave Theme Development - Alternative Start
echo ========================================
echo.
echo Trying multiple connection methods...
echo.

echo Method 1: Standard connection...
shopify theme dev --store 7fa66c-ac.myshopify.com
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Method 1 failed, trying Method 2...
    echo.
    
    echo Method 2: With explicit host/port...
    shopify theme dev --store 7fa66c-ac.myshopify.com --host 127.0.0.1 --port 9292
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo Method 2 failed, trying Method 3...
        echo.
        
        echo Method 3: Force sync disabled...
        shopify theme dev --store 7fa66c-ac.myshopify.com --no-delete
        if %ERRORLEVEL% NEQ 0 (
            echo.
            echo All methods failed. Please run fix-auth.bat first.
            echo.
        )
    )
)

pause
