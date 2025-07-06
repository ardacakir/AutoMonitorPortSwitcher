#!/bin/bash

cd ~/Projects/AutoMonitorPortSwitcher || exit 1

echo "==> Creating target folders..."
mkdir -p linux/src
mkdir -p linux/releases
mkdir -p windows/src
mkdir -p windows/Releases

echo "==> Moving Linux files..."
mv linux/FedoraRelease/* linux/releases/
rmdir linux/FedoraRelease

mv linux/usb_monitor.py linux/src/
mv linux/device_checker.py linux/src/ 2>/dev/null
mv linux/crop_image.py linux/src/ 2>/dev/null
mv linux/monitor.png linux/src/
mv linux/requirements.txt linux/src/

echo "==> Moving Windows files..."
mv usb_monitor.py windows/src/
mv device_checker.py windows/src/ 2>/dev/null
mv monitornew.ico windows/src/
mv usb_monitor.ico windows/src/
mv requirements.txt windows/src/

mv Releases/* windows/Releases/
rmdir Releases

echo "==> Cleaning up loose files from root..."
rm -f usb_monitor.py device_checker.py requirements.txt *.ico

echo "==> Done."