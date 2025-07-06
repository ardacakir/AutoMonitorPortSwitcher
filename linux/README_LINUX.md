# USB Monitor Auto Switcher — Linux Instructions

**Auto Monitor Port Switcher for Fedora Linux**

Automatically switch your monitor input source based on USB device detection — perfect for dual-system setups (e.g., macOS and Fedora) sharing a single display. Supports headless booting, seamless SDDM logins, and KDE tray integration.

---

## 🛠 I2C Permissions Setup (Required for Monitor Switching)

To enable monitor input switching via DDC/CI, the script must access `/dev/i2c-*` devices.  
These device files are usually not accessible by default for regular users, especially after a headless boot.

The installer now includes a **safe and automatic setup** that:

- Ensures the `i2c` group exists
- Adds the current user to the `i2c` group (you may need to reboot or re-login for it to take effect)
- Creates a udev rule to grant correct permissions to `/dev/i2c-*` devices

### Why this is necessary

Without these changes, the service fails to communicate with your monitor over I2C after a headless boot, due to `EACCES(13): Permission denied` errors. This setup guarantees correct access **without disabling SELinux** or requiring dangerous permission changes.

---

## Requirements

Install these dependencies:

```bash
sudo dnf install python3 python3-pip python3-devel \
                 pyudev xdg-utils tk pillow
```

Inside the project folder:

```bash
cd /home/yourname/Projects/AutoMonitorPortSwitcher/
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

> If no `requirements.txt` exists, install manually:  
> `pip install pystray pyudev pillow`

> SELinux is supported and properly handled by the installation script.

---

## Build the Executable

```bash
cd linux/
../venv/bin/pyinstaller --clean --noconsole --onefile \
  --icon=monitor.png \
  --add-data "monitor.png:." \
  --name=usb_monitor_v1.0 \
  usb_monitor.py
```

This creates a standalone file at:

```
linux/dist/usb_monitor_v1.0
```

You can run it directly to test:

```bash
./dist/usb_monitor_v1.0
```

---

## Install as Startup Service

This script now performs a full installation for system-wide use:

- Copies the compiled binary to `/opt/usbmonitor/` with correct SELinux permissions
- Installs or updates the `usb_monitor.service` into the **systemd user service directory** (`~/.config/systemd/user/`)
- Ensures executable is runnable in headless mode at boot
- Enables and starts the service automatically for the current user

The script also searches for the compiled binary in either the current folder or the `FedoraRelease/` folder.

The installation includes automatic setup of I2C access rules and adds the current user to the `i2c` group to allow seamless headless monitor switching.

---

## Features

- ✅ Automatically sets up I2C access rules for seamless headless monitor switching
- ✅ Supports systemd user services for per-user startup
- ✅ Works with SELinux enabled without requiring relaxation
- ✅ KDE tray integration with fallback to AppIndicator under Wayland
- ✅ Uses `tkinter` for settings popup UI
- ✅ Stores settings and logs in `~/.config/USBMonitor/`

---

## Updating to a New Version

1. Build the new version (e.g., `usb_monitor_v1.0`)
2. Run the install script again:

```bash
./install_service.sh
```

That’s it — the service will start the new version on next boot/login.

---

## /etc/systemd/system/usb_monitor.service

The service file is automatically generated from the template under `systemd/usb_monitor.service`  
and installed to `/etc/systemd/system/` by the script. You should not need to edit it manually.

---

### 🧯 Troubleshooting

- **Service fails to start after reboot**  
  - Check if the binary is marked as executable and readable:  
    `ls -l /opt/usbmonitor/usb_monitor_fedora_*`  
  - Run `systemctl --user status usb_monitor.service` for details.

- **Monitor not switching**  
  - Ensure the user is in the `i2c` group:  
    `groups`  
  - Check if `ddcutil detect` lists the monitor.  
  - Make sure `/dev/i2c-*` has the correct permissions.

- **No tray icon after login**  
  - Confirm that the autostart `.desktop` entry exists in `~/.config/autostart/`  
  - You may need to log out and back in once after install.

---

## Uninstall

To disable the service:

```bash
systemctl --user disable usb_monitor.service
systemctl --user stop usb_monitor.service
```

Then delete the executable and service file if desired.

---

## Notes

- Tray icon support uses `pystray` and may fallback to `AppIndicator` under Wayland.  
- GTK or Qt apps can be used for UI; this script currently uses `tkinter` for the settings popup.  
- Lockfile is stored in the script folder, settings and logs in `~/.config/USBMonitor/`.
