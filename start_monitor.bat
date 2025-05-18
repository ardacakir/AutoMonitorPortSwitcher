@echo off
cd /d C:\Projects\AutoMonitorSwitcher
call venv\Scripts\activate.bat
python usb_monitor.py >> logs\log_output.txt 2>&1
