# USB Monitor Auto Switcher — Linux Instructions

This guide explains how to build and install the Linux version of the USB Monitor tool on **Fedora 42 KDE (Wayland)**.  
It uses PyInstaller to create a standalone executable and runs it automatically at user login via `systemd`.

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
- Installs or updates the `usb_monitor.service` into `/etc/systemd/system/`
- Ensures executable is runnable in headless mode at boot
- Enables and starts the service automatically

The script also searches for the compiled binary in either the current folder or the `FedoraRelease/` folder.

---

## Updating to a New Version

1. Build the new version (e.g. `usb_monitor_v1.0`)
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

## Troubleshooting

Check if the service is running:

```bash
systemctl --user status usb_monitor.service
```

See logs:

```bash
journalctl --user -u usb_monitor.service -b
```

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

- Tray icon support uses `pystray` and may fallback to `AppIndicator` under Wayland
- GTK or Qt apps can be used for UI; this script currently uses `tkinter` for the settings popup
- Lockfile is stored in the script folder, settings and logs in `~/.config/USBMonitor/`
