# USB Monitor Port Switcher v1.0.0

This script listens for USB device changes and automatically switches your monitor's input (e.g., HDMI or DisplayPort) using DDC/CI commands. It’s designed for setups where a USB switch shares a monitor between multiple systems.

## Features

- Detects USB connection/disconnection events
- Automatically switches monitor input using [ControlMyMonitor](https://www.nirsoft.net/utils/control_my_monitor.html)
- Fallback polling mechanism if WMI fails

## What's changed

- Linux systemd service support added
- Automatically starts at boot and shows tray icon under Wayland or X11
- Simplified settings and log access from the tray menu
- Log file rotates automatically and can be opened with one click
- New compact and trimmed tray icon

## Files

- `usb_monitor.py` — Main script to run the monitor switcher on Windows and Linux
- `requirements.txt` — Python dependencies for Windows
- `linux/requirements.txt` — Additional dependencies for Linux
- `logs/` — Contains `log_output.txt` and `switch_log.txt` for basic tracking

## Requirements

### Windows
- Windows 10/11
- Python 3.10+
- ControlMyMonitor by NirSoft
- Python modules: `wmi`, `pywin32`

### Linux (Fedora 42+)
- Python 3.12
- `ddcutil`
- `python3-gi`, `libayatana-appindicator3`
- Modules from `linux/requirements.txt`

## Installation

1. **Install dependencies**

```bash
pip install -r requirements.txt
```

2. **Download [ControlMyMonitor.exe](https://www.nirsoft.net/utils/control_my_monitor.html)** and place it in the same folder as the script or adjust the path in `usb_monitor.py`.

3. **Run the script**

```bash
python usb_monitor.py
```

4. **Generate the executable**

```bash
pyinstaller --clean --noconsole --onefile --icon=monitornew.ico --add-data "monitornew.ico;." --name=usb_monitor_v1.0.0 usb_monitor.py
```

### Fedora service

For Fedora 42 you can install the service files provided in the `linux` folder:

```bash
sudo dnf install ddcutil python3-pip
sudo pip3 install -r linux/requirements.txt
sudo bash linux/install_service.sh
```

The service starts on boot and creates a tray icon once a user session is available.

## Logging

Basic logs are written to:

- Windows: `%LOCALAPPDATA%\USBMonitor\logs\switch_log.txt`
- `~/.config/USBMonitor/logs/switch_log.txt` on Linux

Logs rotate automatically once they reach 1 MB, keeping the last three files.

## Notes

- If WMI fails to initialize (common in threads), the script switches to low-frequency polling.
- Monitor input IDs can be configured from the settings popup rather than editing the script directly.

## License

MIT License
