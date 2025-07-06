#!/bin/bash

SERVICE_NAME="usb_monitor.service"
DIST_EXECUTABLE="/opt/usbmonitor/usb_monitor_fedora_v1.1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CANDIDATE1="$SCRIPT_DIR/usb_monitor_fedora_v1.1"
CANDIDATE2="$SCRIPT_DIR/FedoraRelease/usb_monitor_fedora_v1.1"

if [ -f "$CANDIDATE1" ]; then
  LOCAL_EXECUTABLE="$CANDIDATE1"
elif [ -f "$CANDIDATE2" ]; then
  LOCAL_EXECUTABLE="$CANDIDATE2"
else
  echo "❌ Error: Compiled executable not found in either:"
  echo "   $CANDIDATE1"
  echo "   $CANDIDATE2"
  echo "👉 Please build the binary with PyInstaller before running this script."
  exit 1
fi

echo "🔧 Preparing system binary at: $DIST_EXECUTABLE"
echo "Copying binary to /opt/usbmonitor..."
sudo mkdir -p /opt/usbmonitor
sudo cp "$LOCAL_EXECUTABLE" "$DIST_EXECUTABLE"
sudo chmod +x "$DIST_EXECUTABLE"
sudo chcon -t bin_t "$DIST_EXECUTABLE"

SERVICE_SRC="$(pwd)/systemd/$SERVICE_NAME"
SERVICE_DEST="$HOME/.config/systemd/user/$SERVICE_NAME"

echo "⚙️  Setting up systemd user service from: $SERVICE_SRC"
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

echo "🔄 Reloading and starting systemd user service..."
# Reload systemd and enable/start the service
systemctl --user daemon-reload
systemctl --user enable "$SERVICE_NAME"
systemctl --user restart "$SERVICE_NAME"

echo "✅ Service '$SERVICE_NAME' installed and started at: $SERVICE_DEST"
echo "✅ Service installed and started. Check status with:"
echo "   systemctl --user status $SERVICE_NAME"

# --- Add tray autostart ---
AUTOSTART_DIR="$HOME/.config/autostart"
AUTOSTART_FILE="$AUTOSTART_DIR/usb_monitor_tray.desktop"

echo "🖥️  Setting up KDE tray autostart entry..."

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

echo "✅ Autostart desktop entry created at: $AUTOSTART_FILE"