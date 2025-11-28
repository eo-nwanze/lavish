@echo off
echo ========================================
echo Lavish Library - Start Development Environment
echo ========================================
echo.
echo This will start:
echo   1. Django Backend (http://127.0.0.1:8000)
echo   2. Shopify Theme (http://127.0.0.1:9292)
echo.
echo Two terminal windows will open.
echo Press Ctrl+C in each window to stop.
echo ========================================
echo.
pause

REM Start Django Backend in new window
start "Django Backend - Port 8000" cmd /k "cd /d "%~dp0app\lavish_backend" && echo Starting Django Backend... && python manage.py runserver"

REM Wait 3 seconds for Django to start
timeout /t 3 /nobreak

REM Start Shopify Theme in new window
start "Shopify Theme - Port 9292" cmd /k "cd /d "%~dp0app\lavish_frontend" && echo Starting Shopify Theme Dev Server... && shopify theme dev --store 7fa66c-ac.myshopify.com"

echo.
echo ========================================
echo Both servers are starting!
echo ========================================
echo.
echo Django Admin:  http://127.0.0.1:8000/admin/
echo Django API:    http://127.0.0.1:8000/api/
echo Shopify Theme: http://127.0.0.1:9292
echo.
echo Login: admin / vanity007
echo.
echo ========================================
