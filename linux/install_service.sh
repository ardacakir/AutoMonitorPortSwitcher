#!/usr/bin/env bash
set -e

TARGET_DIR=/opt/usbmonitor
sudo mkdir -p "$TARGET_DIR"

sudo cp linux/usb_monitor.py "$TARGET_DIR/usb_monitor.py"
sudo cp monitornew.ico "$TARGET_DIR/monitornew.ico"
sudo cp linux/requirements.txt "$TARGET_DIR/requirements.txt"

sudo cp linux/systemd/usb_monitor.service /etc/systemd/system/usb_monitor.service
sudo systemctl daemon-reload
sudo systemctl enable usb_monitor.service
sudo systemctl start usb_monitor.service
