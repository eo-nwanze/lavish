@echo off
echo ========================================
echo Shopify Theme Development Workflow
echo ========================================
echo.
echo Your Crave Theme is ready for Shopify!
echo.
echo Available Commands:
echo.
echo 1. DEVELOP - Start local development server
echo    shopify theme dev --store 7fa66c-ac.myshopify.com
echo.
echo 2. CHECK - Validate theme code
echo    shopify theme check
echo.
echo 3. PUSH UNPUBLISHED - Upload as new theme
echo    shopify theme push --unpublished
echo.
echo 4. PUSH - Update existing theme
echo    shopify theme push
echo.
echo 5. PUBLISH - Make theme live
echo    shopify theme publish
echo.
echo 6. INFO - Check current store connection
echo    shopify theme info
echo.
echo ========================================
echo.

:menu
echo Choose an option:
echo [1] Start Development Server
echo [2] Check Theme
echo [3] Push as Unpublished Theme
echo [4] Push to Existing Theme
echo [5] Publish Theme
echo [6] Show Theme Info
echo [7] Exit
echo.
set /p choice="Enter your choice (1-7): "

if "%choice%"=="1" goto develop
if "%choice%"=="2" goto check
if "%choice%"=="3" goto push_unpublished
if "%choice%"=="4" goto push
if "%choice%"=="5" goto publish
if "%choice%"=="6" goto info
if "%choice%"=="7" goto exit

echo Invalid choice. Please try again.
goto menu

:develop
echo.
echo Starting development server...
shopify theme dev --store 7fa66c-ac.myshopify.com
goto menu

:check
echo.
echo Checking theme...
shopify theme check
pause
goto menu

:push_unpublished
echo.
echo Pushing as unpublished theme...
echo You'll be prompted to name your theme.
shopify theme push --unpublished
pause
goto menu

:push
echo.
echo Pushing to existing theme...
shopify theme push
pause
goto menu

:publish
echo.
echo Publishing theme...
echo WARNING: This will make your theme live!
set /p confirm="Are you sure? (y/n): "
if /i "%confirm%"=="y" (
    shopify theme publish
) else (
    echo Cancelled.
)
pause
goto menu

:info
echo.
echo Theme information...
shopify theme info
pause
goto menu

:exit
echo.
echo Goodbye!
pause
