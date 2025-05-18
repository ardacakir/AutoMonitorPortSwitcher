import time
import subprocess
import wmi
import os
import sys
from datetime import datetime
from pystray import Icon, Menu, MenuItem
from PIL import Image
import threading
import pythoncom

# Resource path for PyInstaller
def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(__file__), relative_path)

# Constants
LOCK_FILE = os.path.join(os.path.dirname(__file__), "usb_monitor.lock")
KEYBOARD_IDENTIFIER = "VID_04D9&PID_A1DF"
CONTROL_EXE = r"C:\Projects\Tools\ControlMyMonitor\ControlMyMonitor.exe"
MONITOR_ID = "M3LMQS370483"
DISPLAYPORT_INPUT = "15"
HDMI_INPUT = "18"
APP_DATA = os.path.expanduser("~/AppData/Local/USBMonitor")
LOG_FILE = os.path.join(APP_DATA, "logs", "switch_log.txt")

icon = None
current_manual_state = False

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
    log_dir = os.path.join(APP_DATA, "logs")
    try:
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} - {message}\n")
    except Exception as e:
        fallback_log = os.path.join(os.path.dirname(__file__), "log_error.txt")
        try:
            with open(fallback_log, "a", encoding="utf-8") as f:
                f.write(f"{timestamp} - Logging failed: {e}\n")
                f.write(f"{timestamp} - Attempted log path: {LOG_FILE}\n")
        except:
            pass

def is_keyboard_connected():
    for _ in range(3):
        try:
            c = wmi.WMI()
            devices = [usb.DeviceID for usb in c.Win32_USBHub()]
            for device in devices:
                if KEYBOARD_IDENTIFIER.lower() in device.lower():
                    return True
            return False
        except:
            time.sleep(0.5)

    log_event("WMI failed after 3 retries, assuming keyboard not connected")
    return False

def get_current_input():
    # Get the current input of the monitor using ControlMyMonitor.exe.
    command = [CONTROL_EXE, "/GetValue", MONITOR_ID, "60"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, cwd=os.path.dirname(CONTROL_EXE), check=True)
        # The output is the current input value (e.g., "15" for DP, "18" for HDMI)
        current_input = result.stdout.strip()
        log_event(f"Current monitor input: {current_input}")
        return current_input
    except subprocess.CalledProcessError as e:
        log_event(f"Failed to get current input: {e}")
        return None
    except Exception as e:
        log_event(f"Error getting current input: {e}")
        return None

def switch_input(input_code):
    # Force the monitor to switch to the specified input.
    command = [CONTROL_EXE, "/SetValue", MONITOR_ID, "60", str(input_code)]
    log_event(f"Forcing DDC switch: {' '.join(command)}")
    for _ in range(3):
        subprocess.run(command, check=False, cwd=os.path.dirname(CONTROL_EXE))
        time.sleep(0.5)

def toggle_input(icon_obj, item):
    global current_manual_state, icon
    current_manual_state = not current_manual_state
    if current_manual_state:
        log_event("Manual switch → DisplayPort")
        switch_input(DISPLAYPORT_INPUT)
        icon.title = "USB Monitor (DisplayPort)"
    else:
        log_event("Manual switch → HDMI 2")
        switch_input(HDMI_INPUT)
        icon.title = "USB Monitor (HDMI 2)"

def main_loop():
    pythoncom.CoInitialize()
    try:
        last_state = None
        time.sleep(10)
        while True:
            connected = is_keyboard_connected()
            if connected is None:
                time.sleep(2)
                continue
            if last_state is None:
                if connected:
                    log_event("Initial check: Keyboard detected -> using DisplayPort")
                    time.sleep(1)
                    switch_input(DISPLAYPORT_INPUT)
                else:
                    log_event("Initial check: Keyboard not detected -> using HDMI 2")
                    time.sleep(1)
                    switch_input(HDMI_INPUT)
                last_state = connected
            elif connected != last_state:
                if connected:
                    log_event("Keyboard detected -> switching to DisplayPort")
                    time.sleep(1)
                    switch_input(DISPLAYPORT_INPUT)
                    icon.title = "USB Monitor (DisplayPort)"
                else:
                    log_event("Keyboard not detected -> switching to HDMI 2")
                    time.sleep(1)
                    switch_input(HDMI_INPUT)
                    icon.title = "USB Monitor (HDMI 2)"
                last_state = connected
            time.sleep(2)
    finally:
        pythoncom.CoUninitialize()

def create_tray_icon():
    global icon
    icon_path = get_resource_path('monitorsw.ico')
    try:
        image = Image.open(icon_path)
    except Exception as e:
        log_event(f"Failed to load tray icon: {e}")
        image = Image.new("RGB", (64, 64), color=(0, 0, 0))
    menu = Menu(
        MenuItem('Switch Monitor Port', toggle_input),
        MenuItem('Stop Service', quit_app)
    )
    icon = Icon("USBMonitor", image, "USB Monitor", menu)
    threading.Thread(target=main_loop, daemon=True).start()
    icon.run()

def quit_app(icon, item):
    log_event("Tray icon exit requested.")
    remove_lock_file()
    icon.stop()
    sys.exit(0)

if __name__ == "__main__":
    check_single_instance()
    log_event("Script started")
    try:
        create_tray_icon()
    except KeyboardInterrupt:
        log_event("Script terminated by user.")
    except Exception as e:
        log_event(f"Script crashed: {e}")
    finally:
        remove_lock_file()