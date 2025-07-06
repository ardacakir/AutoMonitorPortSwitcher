#!/bin/bash

SERVICE_NAME="usb_monitor.service"
DIST_EXECUTABLE="/opt/usbmonitor/usb_monitor_fedora_v1.1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CANDIDATE1="$SCRIPT_DIR/usb_monitor_fedora_v1.1"
CANDIDATE2="$SCRIPT_DIR/releases/usb_monitor_fedora_v1.1"

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
echo "🛠️  Checking I2C group permissions..."

if ! getent group i2c >/dev/null; then
    echo "➕ Creating 'i2c' group..."
    sudo groupadd i2c
else
    echo "✅ 'i2c' group already exists."
fi

if groups $USER | grep -qw i2c; then
    echo "✅ User '$USER' already in 'i2c' group."
else
    echo "➕ Adding user '$USER' to 'i2c' group..."
    sudo usermod -aG i2c $USER
    echo "⚠️  You must log out and back in (or reboot) for group changes to apply."
fi

I2C_RULE_PATH="/etc/udev/rules.d/45-ddcutil-i2c.rules"
if [ ! -f "$I2C_RULE_PATH" ]; then
    echo "➕ Creating udev rule for i2c device permissions..."
    echo 'KERNEL=="i2c-[0-9]*", GROUP="i2c", MODE="0660"' | sudo tee "$I2C_RULE_PATH" > /dev/null
    echo "🔄 Reloading udev rules..."
    sudo udevadm control --reload-rules
    sudo udevadm trigger
else
    echo "✅ Udev rule already exists at $I2C_RULE_PATH"
fi

echo "🧼 Checking for running instances of the previous binary..."
PIDS=$(sudo fuser "$DIST_EXECUTABLE" 2>/dev/null)

if [ -n "$PIDS" ]; then
    echo "🔪 Found running instances: $PIDS"
    echo "   Terminating them to avoid file lock issues..."
    sudo fuser -k "$DIST_EXECUTABLE" > /dev/null 2>&1 || true
    echo ""
else
    echo "✅ No running instances found."
fi

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