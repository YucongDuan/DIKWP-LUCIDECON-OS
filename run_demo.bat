@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (py -3 lucidecon.pyz demo --output "outputs\demo_%RANDOM%") else (python lucidecon.pyz demo --output "outputs\demo_%RANDOM%")
pause
