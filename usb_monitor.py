import time
import subprocess
import wmi
import os
import sys
from datetime import datetime


LOCK_FILE = os.path.join(os.path.dirname(__file__), "usb_monitor.lock")

# Unique string from your keyboard's USB DeviceID
KEYBOARD_IDENTIFIER = "VID_04D9&PID_A1DF"

# Path to ControlMyMonitor.exe
CONTROL_EXE = r"C:\Projects\Tools\ControlMyMonitor\ControlMyMonitor.exe"

# Monitor identifier (use serial number for accuracy)
MONITOR_ID = "M3LMQS370483"

# Input source values: 15 = DisplayPort, 18 = HDMI 2
DISPLAYPORT_INPUT = "15"
HDMI_INPUT = "18"

# Log file location
LOG_FILE = os.path.join(os.path.dirname(__file__), "logs", "switch_log.txt")
LOCK_FILE = os.path.join(os.path.dirname(__file__), "usb_monitor.lock")

def check_single_instance():
    if os.path.exists(LOCK_FILE):
        print("Another instance is already running. Exiting.")
        sys.exit(0)
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))

def remove_lock_file():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

def log_event(message):
    log_dir = os.path.dirname(LOG_FILE)
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} - {message}\n")

def is_keyboard_connected():
    try:
        c = wmi.WMI()
        devices = [usb.DeviceID for usb in c.Win32_USBHub()]
        for device in devices:
            if KEYBOARD_IDENTIFIER.lower() in device.lower():
                return True
    except Exception as e:
        log_event(f"WMI error: {e}")
    return False

def switch_input(input_code):
    command = [
        CONTROL_EXE,
        "/SetValue",
        MONITOR_ID,
        "60",
        str(input_code)
    ]

    print(f"Running DDC command: {' '.join(command)}")
    log_event(f"Running DDC command: {' '.join(command)}")

    attempts = 3 
    for i in range(attempts):
        subprocess.run(command, check=False, cwd=os.path.dirname(CONTROL_EXE))
        time.sleep(0.5)

def main_loop():
    last_state = None
    time.sleep(10)
    while True:
        connected = is_keyboard_connected()
        if connected != last_state:
            if connected:
                log_event("Keyboard detected -> switching to DisplayPort")
                time.sleep(1)  # short grace period
                switch_input(DISPLAYPORT_INPUT)
            else:
                log_event("Keyboard not detected -> switching to HDMI 2")
                time.sleep(1)  # short grace period
                switch_input(HDMI_INPUT)

            # ✅ Always update after handling the state change
            last_state = connected

        time.sleep(2)

if __name__ == "__main__":
    check_single_instance()
    log_event("Script started")
    try:
        main_loop()
    except KeyboardInterrupt:
        log_event("Script terminated by user.")
    except Exception as e:
        log_event(f"Script crashed: {e}")
    finally:
        remove_lock_file()
