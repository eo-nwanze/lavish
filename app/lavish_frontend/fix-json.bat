@echo off
echo ========================================
echo Fixing JSON Upload Errors
echo ========================================
echo.

echo Restoring original locale file...
copy "C:\Users\eonwa\Desktop\Lavish Library\app\crave_theme\locales\en.default.json" "C:\Users\eonwa\Desktop\Lavish Library\app\lavish_frontend\locales\en.default.json" /Y

echo.
echo Validating JSON...
powershell -Command "$content = Get-Content 'locales\en.default.json' -Raw; try { $json = $content | ConvertFrom-Json; Write-Host 'JSON is valid' } catch { Write-Host 'JSON Error:' $_.Exception.Message }"

echo.
echo Checking theme...
shopify theme check | findstr /C:"TranslationKeyExists" /C:"MissingAsset" /C:"JSON"

echo.
echo ========================================
echo JSON Fix Complete
echo ========================================
pause
