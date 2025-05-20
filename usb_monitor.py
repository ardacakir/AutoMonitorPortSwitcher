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
import json
from tkinter import messagebox  # Import here to avoid issues in --noconsole builds
import tkinter as tk

# Resource path for PyInstaller
def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(__file__), relative_path)

# Constants
LOCK_FILE = os.path.join(os.path.dirname(__file__), "usb_monitor.lock")
#KEYBOARD_IDENTIFIER = "VID_04D9&PID_A1DF"
CONTROL_EXE = r"C:\Projects\Tools\ControlMyMonitor\ControlMyMonitor.exe"
MONITOR_ID = "M3LMQS370483"
#INPUT_WHEN_CONNECTED = "15"
#INPUT_WHEN_DISCONNECTED = "18"
APP_DATA = os.path.expanduser("~/AppData/Local/USBMonitor")
LOG_FILE = os.path.join(APP_DATA, "logs", "switch_log.txt")
SETTINGS_FILE = os.path.join(APP_DATA, "settings.json")

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
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        os.makedirs(log_dir, exist_ok=True)
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

def show_settings_popup():
    def save_settings():
        settings = {
            "keyboard_id": keyboard_id_entry.get().strip(),
            "input_connected": input_connected_entry.get().strip(),
            "input_disconnected": input_disconnected_entry.get().strip()
        }
        os.makedirs(APP_DATA, exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
        messagebox.showinfo("USB Monitor", "Settings saved successfully.")
        root.destroy()

    root = tk.Tk()
    root.title("USB Monitor Settings")
    root.geometry("300x200")
    root.resizable(False, False)

    tk.Label(root, text="Keyboard USB ID:").pack()
    keyboard_id_entry = tk.Entry(root)
    keyboard_id_entry.insert(0, "VID_04D9&PID_A1DF")
    keyboard_id_entry.pack()

    tk.Label(root, text="Input Code (when Keyboard is CONNECTED):").pack()
    input_connected_entry = tk.Entry(root)
    input_connected_entry.insert(0, "15")
    input_connected_entry.pack()

    tk.Label(root, text="Input Code (when Keyboard is NOT connected):").pack()
    input_disconnected_entry = tk.Entry(root)
    input_disconnected_entry.insert(0, "18")
    input_disconnected_entry.pack()

    tk.Button(root, text="Save", command=save_settings).pack(pady=10)
    root.mainloop()

show_settings_popup()

with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
    config = json.load(f)

KEYBOARD_IDENTIFIER = config.get("keyboard_id", "VID_04D9&PID_A1DF")
INPUT_WHEN_CONNECTED = config.get("input_connected", "15")
INPUT_WHEN_DISCONNECTED = config.get("input_disconnected", "18")

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
        switch_input(INPUT_WHEN_CONNECTED)
        icon.title = "USB Monitor (DisplayPort)"
    else:
        log_event("Manual switch → HDMI 2")
        switch_input(INPUT_WHEN_DISCONNECTED)
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
                    switch_input(INPUT_WHEN_CONNECTED)
                else:
                    log_event("Initial check: Keyboard not detected -> using HDMI 2")
                    time.sleep(1)
                    switch_input(INPUT_WHEN_DISCONNECTED)
                last_state = connected
            elif connected != last_state:
                if connected:
                    log_event("Keyboard detected -> switching to connected input")
                    time.sleep(1)
                    switch_input(INPUT_WHEN_CONNECTED)
                    icon.title = f"USB Monitor (Connected: {INPUT_WHEN_CONNECTED})"
                else:
                    log_event("Keyboard not detected -> switching to disconnected input")
                    time.sleep(1)
                    switch_input(INPUT_WHEN_DISCONNECTED)
                    icon.title = f"USB Monitor (Disconnected: {INPUT_WHEN_DISCONNECTED})"
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
        Menu.SEPARATOR,
        MenuItem('Edit Settings', lambda icon, item: threading.Thread(target=show_settings_popup).start()),
        Menu.SEPARATOR,
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