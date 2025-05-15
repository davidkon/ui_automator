@echo off
setlocal EnableDelayedExpansion

:: Get the filter parameter (default to "location" if not provided)
set "FILTER=%~1"
if "%FILTER%"=="" set "FILTER=location"

title ADB Logcat Monitor (%FILTER%)
color 0F
echo Connecting to Android device on localhost...
adb -s localhost connect localhost
echo.
echo Getting root access...
adb -s localhost root
echo.
echo Starting logcat stream filtered for "%FILTER%"...
echo --------------------------------------------------

:: Enable ANSI color codes in Windows console
reg add HKCU\Console /v VirtualTerminalLevel /t REG_DWORD /d 1 /f >nul 2>&1

:: Create a simple PowerShell script for coloring the output
echo $filter = "%FILTER%" > "%TEMP%\logcat_color.ps1"
echo $ErrorActionPreference = "SilentlyContinue" >> "%TEMP%\logcat_color.ps1"
echo while ($true) { >> "%TEMP%\logcat_color.ps1"
echo   $line = [Console]::In.ReadLine() >> "%TEMP%\logcat_color.ps1"
echo   if ($line -match $filter) { >> "%TEMP%\logcat_color.ps1"
echo     if ($line -match " E ") { >> "%TEMP%\logcat_color.ps1"
echo       Write-Host $line -ForegroundColor Red >> "%TEMP%\logcat_color.ps1"
echo     } elseif ($line -match "true") { >> "%TEMP%\logcat_color.ps1"
echo       Write-Host $line -ForegroundColor Green >> "%TEMP%\logcat_color.ps1"
echo     } elseif ($line -match "false") { >> "%TEMP%\logcat_color.ps1"
echo       Write-Host $line -ForegroundColor Yellow >> "%TEMP%\logcat_color.ps1"
echo     } else { >> "%TEMP%\logcat_color.ps1"
echo       Write-Host $line >> "%TEMP%\logcat_color.ps1"
echo     } >> "%TEMP%\logcat_color.ps1"
echo   } >> "%TEMP%\logcat_color.ps1"
echo } >> "%TEMP%\logcat_color.ps1"

:: Run ADB logcat and pipe through PowerShell for filtering and coloring
adb -s localhost shell logcat | powershell -ExecutionPolicy Bypass -File "%TEMP%\logcat_color.ps1"

:: Clean up
del "%TEMP%\logcat_color.ps1" >nul 2>&1

endlocal