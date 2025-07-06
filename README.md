# Auto Monitor Port Switcher

Auto-switch your monitor input based on USB device detection.  
Built for **Fedora Linux + KDE**, this utility lets you share a single display between a Linux PC and another device (e.g., Mac Mini) using a USB switch.

> **Linux-only development from v1.0 onward.**  
> Legacy Windows versions are archived under the `windows/` folder for reference only.

---

## Purpose

This tool detects the presence of a specific USB device (e.g. your keyboard) and switches the monitor’s input source automatically using `ddcutil`.

Perfect for:
- **Dual-system setups** (e.g. Fedora + macOS)
- **Single-monitor workflows**
- **Headless boots** with USB switch reconnect
- Seamless **KDE tray integration**

---

## Linux Installation (Fedora/KDE)

See full steps in [`linux/README_LINUX.md`](linux/README_LINUX.md)

### 1. Dependencies

```bash
sudo dnf install python3 python3-pip python3-devel \
                 pyudev xdg-utils tk pillow
```

### 2. Create virtual environment & install

```bash
cd linux/
python3 -m venv venv
source venv/bin/activate
pip install -r src/requirements.txt
```

---

### 3. Build the Executable

```bash
cd linux/
../venv/bin/pyinstaller --clean --noconsole --onefile \
  --icon=src/monitor.png \
  --add-data "src/monitor.png:." \
  --name=usb_monitor_fedora_v1.1 \
  src/usb_monitor.py
```

You’ll find the result in `linux/dist/`. Test it by running:

```bash
./dist/usb_monitor_fedora_v1.1
```

---

### 4. Install as a systemd service

```bash
./install_service.sh
```

This will:
- Copy the binary to `/opt/usbmonitor/`
- Set up I2C access and `udev` rules
- Install and enable the `usb_monitor.service`
- Ensure the app autostarts with KDE tray support

By default the service is installed as a **systemd user service** under
`~/.config/systemd/user/`. User services start when your systemd user
instance is running – typically after you log in (graphical session or
via SSH). If you want the monitor switcher to run automatically at boot
even when no session is active, enable *lingering* for your account:

```bash
sudo loginctl enable-linger <yourusername>
```

Replace `<yourusername>` with your Linux user name. This makes your
systemd user instance start during boot so the service runs without
requiring a login.

---

## Features

- KDE tray icon with automatic input switching
- Auto-setup of `i2c` permissions for `ddcutil`
- Works during headless boots (e.g. after USB reconnect)
- Built-in `tkinter` popup to change USB ID or monitor ports
- SELinux-friendly — no permission hacks required

---

## Settings & Logs

- Config: `~/.config/USBMonitor/settings.json`
- Logs: `~/.config/USBMonitor/logs/`

---

## Uninstall

```bash
systemctl --user disable usb_monitor.service
systemctl --user stop usb_monitor.service
rm -rf /opt/usbmonitor/
```

---

## Legacy Windows Builds

Earlier Windows build is still available under:

```
windows/Releases/
```

This `.exe` file is frozen using `pyinstaller` but **no longer maintained**.

You can inspect the legacy Python source at:

```
windows/src/
```

---

## License

MIT License – see [LICENSE](LICENSE) file.

---

## Tags

`linux` · `fedora` · `monitor` · `ddcutil` · `kde` · `auto-switch` · `usb`

---

> This project is now Linux-only but Windows version was working as of Win11 24H2.  
> Stable and actively maintained for Fedora KDE (Wayland).  
> Designed with ❤️ by [@ardacakir](https://github.com/ardacakir)
