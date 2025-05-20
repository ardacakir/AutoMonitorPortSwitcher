# USB Monitor Port Switcher v0.6.3

This script listens for USB device changes and automatically switches your monitor's input (e.g., HDMI or DisplayPort) using DDC/CI commands. It’s designed for setups where a USB switch shares a monitor between multiple systems.

## Features

- Detects USB connection/disconnection events
- Automatically switches monitor input using [ControlMyMonitor](https://www.nirsoft.net/utils/control_my_monitor.html)
- Fallback polling mechanism if WMI fails

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
pyinstaller --clean --noconsole --onefile --icon=monitorsw.ico --add-data "monitorsw.ico;." --name=usb_monitor_v0.8 usb_monitor.py
```

## Logging

Basic logs are written to:

- `C:\Users\USER_NAME\AppData\Local\USBMonitor\logs\switch_log.txt`

## Notes

- If WMI fails to initialize (common in threads), the script switches to low-frequency polling.
- You can change monitor input IDs or device name directly in `usb_monitor.py` if needed.

## License

MIT License