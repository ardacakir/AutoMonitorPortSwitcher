#!/bin/bash

SERVICE_NAME="usb_monitor.service"
DIST_EXECUTABLE="$(pwd)/FedoraRelease/usb_monitor_v0.10.1"
SERVICE_SRC="$(pwd)/systemd/$SERVICE_NAME"
SERVICE_DEST="$HOME/.config/systemd/user/$SERVICE_NAME"

echo "Installing $SERVICE_NAME..."

# Ensure user systemd directory exists
mkdir -p "$HOME/.config/systemd/user/"

# Inject correct ExecStart path into a temp service file
TEMP_SERVICE=$(mktemp)
sed "s|^ExecStart=.*|ExecStart=$DIST_EXECUTABLE|" "$SERVICE_SRC" > "$TEMP_SERVICE"

# Copy to final location
cp "$TEMP_SERVICE" "$SERVICE_DEST"
rm "$TEMP_SERVICE"

# Reload systemd and enable/start the service
systemctl --user daemon-reload
systemctl --user enable "$SERVICE_NAME"
systemctl --user restart "$SERVICE_NAME"

echo "✅ Service installed and started. Check status with:"
echo "   systemctl --user status $SERVICE_NAME"
