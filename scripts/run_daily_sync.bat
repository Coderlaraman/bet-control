@echo off
cd /d "%~dp0.."
call .venv\Scripts\activate.bat
echo Starting Daily Sync...
python scripts/daily_sync.py
echo Sync Completed.
