# USB Monitor Port Switcher v0.9.0

This script listens for USB device changes and automatically switches your monitor's input (e.g., HDMI or DisplayPort) using DDC/CI commands. It’s designed for setups where a USB switch shares a monitor between multiple systems.

## Features

- Detects USB connection/disconnection events
- Automatically switches monitor input using [ControlMyMonitor](https://www.nirsoft.net/utils/control_my_monitor.html)
- Fallback polling mechanism if WMI fails

## What's changed

- Monitor ID setting added
Users can now define monitor_id (e.g., \\.\DISPLAY1\Monitor0) in the Settings UI — no hardcoded serials needed.
- Settings window layout improved
Switched to grid() layout for cleaner alignment and spacing.
- "Test DisplayPort" and "Test HDMI" buttons
Instantly try monitor input switching from the Settings window.
- Save button made larger and centered
For better visual balance and emphasis.
- "Show Logs" option in tray menu
Opens switch_log.txt directly from system tray.
- New colorful tray icon
Replaced default .ico with a gradient-based USB/monitor icon for better visibility and uniqueness.

## Files

- `usb_monitor.py` — Main script to run the monitor switcher
- `requirements.txt` — Python dependencies
- `monitorsw.ico` — Application icon
- `logs/` — Contains `log_output.txt` and `switch_log.txt` for basic tracking

## Requirements

- Windows 10/11
- Python 3.10+
- ControlMyMonitor by NirSoft
- Python modules: `wmi`, `pywin32`

### Linux (Fedora 42)

- Python 3.12
- `ddcutil` command line tool
- Python modules from `linux/requirements.txt`
- `python3-gi` and an AppIndicator library such as `libayatana-appindicator3` are required when running under Wayland

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
pyinstaller --clean --noconsole --onefile --icon=monitornew.ico --add-data "monitornew.ico;." --name=usb_monitor_v0.9.1 usb_monitor.py
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

- `C:\Users\USER_NAME\AppData\Local\USBMonitor\logs\switch_log.txt`
- `~/.config/USBMonitor/logs/switch_log.txt` on Linux

## Notes

- If WMI fails to initialize (common in threads), the script switches to low-frequency polling.
- You can change monitor input IDs or device name directly in `usb_monitor.py` if needed.

## License

MIT License
