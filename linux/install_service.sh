#!/bin/bash

SERVICE_NAME="usb_monitor.service"
DIST_EXECUTABLE="$(pwd)/FedoraRelease/usb_monitor_fedora_v1.0.2"
SERVICE_SRC="$(pwd)/systemd/$SERVICE_NAME"
SERVICE_DEST="$HOME/.config/systemd/user/$SERVICE_NAME"

echo "Installing $SERVICE_NAME..."

# Ensure user systemd directory exists
mkdir -p "$HOME/.config/systemd/user/"

# Inject correct ExecStart path into a temp service file
TEMP_SERVICE=$(mktemp)
trap 'rm -f "$TEMP_SERVICE"' EXIT
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

# --- Add tray autostart ---
AUTOSTART_DIR="$HOME/.config/autostart"
AUTOSTART_FILE="$AUTOSTART_DIR/usb_monitor_tray.desktop"

echo "Setting up KDE tray autostart..."

mkdir -p "$AUTOSTART_DIR"

cat > "$AUTOSTART_FILE" <<EOF
[Desktop Entry]
Type=Application
Exec=$DIST_EXECUTABLE
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=USB Monitor Tray
Comment=Shows tray icon for input switcher
EOF

echo "✅ Autostart entry created at: $AUTOSTART_FILE"