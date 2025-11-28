@echo off
echo ========================================
echo Starting Clean Crave Theme Development
echo ========================================
echo.

echo Step 1: Ensuring clean JSON files...
copy "C:\Users\eonwa\Desktop\Lavish Library\app\crave_theme\locales\en.default.json" "locales\en.default.json" /Y >nul 2>&1

echo Step 2: Quick theme validation...
shopify theme check --fail-level=error

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo WARNING: Theme has errors. Continue anyway? (y/n)
    set /p continue="Continue: "
    if /i not "%continue%"=="y" (
        echo Cancelled.
        pause
        exit /b 1
    )
)

echo.
echo Step 3: Starting development server...
echo.
echo URLs will be available at:
echo - Local: http://127.0.0.1:9292
echo - Store: https://7fa66c-ac.myshopify.com/?preview_theme_id=XXXXX
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

shopify theme dev --store 7fa66c-ac.myshopify.com
