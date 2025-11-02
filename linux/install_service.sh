#!/bin/bash
set -euo pipefail

SERVICE_NAME="usb_monitor.service"
DIST_EXECUTABLE="/opt/usbmonitor/usb_monitor_fedora_v1.1.4"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CANDIDATE1="$SCRIPT_DIR/usb_monitor_fedora_v1.1"
CANDIDATE2="$SCRIPT_DIR/releases/usb_monitor_fedora_v1.1.4"

# --- pick executable ---
if [[ -f "$CANDIDATE1" ]]; then
  LOCAL_EXECUTABLE="$CANDIDATE1"
elif [[ -f "$CANDIDATE2" ]]; then
  LOCAL_EXECUTABLE="$CANDIDATE2"
else
  echo "❌ Error: compiled executable not found:"
  echo "   $CANDIDATE1"
  echo "   $CANDIDATE2"
  exit 1
fi

echo "🔧 Preparing system binary at: $DIST_EXECUTABLE"
echo "🛠️  Ensuring i2c group + udev rules..."

# 1) Ensure i2c is a *system* group so udev accepts it
if ! getent group i2c >/dev/null; then
  echo "➕ Creating system group 'i2c'..."
  sudo groupadd -r i2c
else
  # If it exists but isn't system, that's fine too; udev cares that it exists.
  echo "✅ Group 'i2c' exists."
fi

# 2) Ensure current user is in i2c
if id -nG "$USER" | grep -qw i2c; then
  echo "✅ User '$USER' already in 'i2c'."
else
  echo "➕ Adding '$USER' to 'i2c'..."
  sudo usermod -aG i2c "$USER"
  echo "⚠️  Log out/in (or 'newgrp i2c') so your session picks up the group."
fi

# 3) Correct udev rules (subsystem match + durable group perms + ACL)
#    Use a single high-priority file to win over vendor rules.
UDEV_RULE="/etc/udev/rules.d/99-i2c-dev.rules"
sudo tee "$UDEV_RULE" >/dev/null <<'RULE'
# Ensure /dev/i2c-* are usable by group i2c, even pre-login
SUBSYSTEM=="i2c-dev", KERNEL=="i2c-[0-9]*", GROUP="i2c", MODE="0660"
# Belt-and-braces to survive later rule clobbering or ACL masks:
SUBSYSTEM=="i2c-dev", KERNEL=="i2c-[0-9]*", RUN+="/usr/bin/setfacl -m g::rw /dev/%k"
RULE
echo "✅ Udev rule written to $UDEV_RULE"

# 4) Reload + retrigger only the needed devices
sudo udevadm control --reload-rules
# Ensure module present; harmless if already loaded
sudo /sbin/modprobe i2c_dev || true
# Retrigger the i2c-dev class so new perms apply immediately
sudo udevadm trigger --subsystem-match=i2c-dev

# 5) Verify one representative node (best-effort)
if [[ -e /dev/i2c-6 ]]; then
  echo "🔎 Checking /dev/i2c-6 permissions..."
  ls -l /dev/i2c-6
  getfacl /dev/i2c-6 | sed -n '1,20p'
fi

# --- install binary ---
echo "📦 Installing binary..."
sudo install -D -m 0755 "$LOCAL_EXECUTABLE" "$DIST_EXECUTABLE"
# SELinux context (ok to skip if not enforcing on /opt, but keep to be safe)
sudo chcon -t bin_t "$DIST_EXECUTABLE" || true

# --- systemd user service ---
SERVICE_SRC="$SCRIPT_DIR/systemd/$SERVICE_NAME"
SERVICE_DEST="$HOME/.config/systemd/user/$SERVICE_NAME"
mkdir -p "$HOME/.config/systemd/user/"

echo "⚙️  Installing user service to $SERVICE_DEST ..."
TEMP_SERVICE=$(mktemp)
trap 'rm -f "$TEMP_SERVICE"' EXIT
sed "s|^ExecStart=.*|ExecStart=$DIST_EXECUTABLE|" "$SERVICE_SRC" > "$TEMP_SERVICE"
cp "$TEMP_SERVICE" "$SERVICE_DEST"

systemctl --user daemon-reload
systemctl --user enable "$SERVICE_NAME"
systemctl --user restart "$SERVICE_NAME"

echo "✅ Service installed and started."
echo "ℹ️  Check status: systemctl --user status $SERVICE_NAME"
echo "ℹ️  Logs:        journalctl --user -u $SERVICE_NAME -f"

# --- optional: autostart tray icon ---
AUTOSTART_DIR="$HOME/.config/autostart"
AUTOSTART_FILE="$AUTOSTART_DIR/usb_monitor_tray.desktop"
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
