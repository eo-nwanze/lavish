@echo off
echo ========================================
echo Lavish Library - Quick Start with UV
echo ========================================
echo.
echo This script will:
echo   1. Setup virtual environment with uv
echo   2. Install dependencies
echo   3. Start Django on port 8003
echo.
echo Make sure uv is installed first!
echo ========================================
echo.
pause

echo Installing uv (if not installed)...
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

echo.
echo Setting up Django Backend...
cd /d "%~dp0app\lavish_backend"

echo Creating virtual environment with uv...
uv venv

echo Activating virtual environment...
call .venv\Scripts\activate

echo Installing core dependencies with uv...
uv pip install django==4.2.23
uv pip install djangorestframework==3.16.0
uv pip install django-cors-headers==4.7.0
uv pip install python-dotenv==1.0.0
uv pip install requests==2.31.0
uv pip install django-environ==0.12.0
uv pip install whitenoise==6.9.0

echo Running migrations...
python manage.py migrate

echo.
echo ========================================
echo Setup Complete! Starting server...
echo ========================================
echo.
echo Django will start on: http://127.0.0.1:8003
echo Admin access: http://127.0.0.1:8003/admin/
echo Login: admin / vanity007
echo.
echo ========================================

python manage.py runserver 127.0.0.1:8003
