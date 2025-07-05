#!/usr/bin/env python3
import os

# Use AppIndicator backend under Wayland for tray icon support
if os.environ.get("XDG_SESSION_TYPE") == "wayland":
    os.environ.setdefault("PYSTRAY_BACKEND", "appindicator")

import sys
import time
import json
import subprocess
from datetime import datetime
import threading

import pyudev
from pystray import Icon, Menu, MenuItem
from PIL import Image
import tkinter as tk
from tkinter import messagebox

# Basic paths
LOCK_FILE = os.path.join(os.path.dirname(__file__), "usb_monitor.lock")
APP_DATA = os.path.expanduser("~/.config/USBMonitor")
LOG_FILE = os.path.join(APP_DATA, "logs", "switch_log.txt")
SETTINGS_FILE = os.path.join(APP_DATA, "settings.json")

icon = None
current_manual_state = False

DDCUTIL_CMD = "ddcutil"


def check_single_instance():
    if os.path.exists(LOCK_FILE):
        print("Another instance is already running. Exiting.")
        sys.exit(0)
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))


def remove_lock_file():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)


def log_event(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_dir = os.path.join(APP_DATA, "logs")
    os.makedirs(log_dir, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} - {message}\n")


def open_log_file():
    if os.path.exists(LOG_FILE):
        subprocess.Popen(["xdg-open", LOG_FILE])
    else:
        messagebox.showinfo("USB Monitor", "Log file not found.")


def ensure_settings_file():
    if not os.path.exists(SETTINGS_FILE):
        show_settings_popup()


def show_settings_popup():
    existing = {
        "monitor_bus": "1",
        "keyboard_id": "046d:c31c",
        "input_connected": "15",
        "input_disconnected": "18",
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                existing.update(json.load(f))
        except Exception:
            pass

    def save_settings():
        settings = {
            "monitor_bus": monitor_bus_entry.get().strip(),
            "keyboard_id": keyboard_id_entry.get().strip(),
            "input_connected": input_connected_entry.get().strip(),
            "input_disconnected": input_disconnected_entry.get().strip(),
        }
        os.makedirs(APP_DATA, exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
        messagebox.showinfo("USB Monitor", "Settings saved successfully.")
        root.destroy()

    root = tk.Tk()
    root.title("USB Monitor Settings")
    root.resizable(False, False)

    padding = {"padx": 8, "pady": 4}
    tk.Label(root, text="Monitor Bus:").grid(row=0, column=0, sticky="w", **padding)
    monitor_bus_entry = tk.Entry(root, width=8)
    monitor_bus_entry.insert(0, existing.get("monitor_bus", "1"))
    monitor_bus_entry.grid(row=0, column=1, **padding)

    tk.Label(root, text="Keyboard USB ID (VID:PID):").grid(row=1, column=0, sticky="w", **padding)
    keyboard_id_entry = tk.Entry(root, width=16)
    keyboard_id_entry.insert(0, existing.get("keyboard_id"))
    keyboard_id_entry.grid(row=1, column=1, **padding)

    tk.Label(root, text="Input Code (Connected):").grid(row=2, column=0, sticky="w", **padding)
    input_connected_entry = tk.Entry(root, width=8)
    input_connected_entry.insert(0, existing.get("input_connected"))
    input_connected_entry.grid(row=2, column=1, **padding)

    tk.Label(root, text="Input Code (Disconnected):").grid(row=3, column=0, sticky="w", **padding)
    input_disconnected_entry = tk.Entry(root, width=8)
    input_disconnected_entry.insert(0, existing.get("input_disconnected"))
    input_disconnected_entry.grid(row=3, column=1, **padding)

    tk.Button(root, text="Save", width=20, command=save_settings).grid(row=4, column=0, columnspan=2, pady=12)

    root.mainloop()


def load_config():
    ensure_settings_file()
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


CONFIG = load_config()
MONITOR_BUS = CONFIG.get("monitor_bus", "1")
KEYBOARD_IDENTIFIER = CONFIG.get("keyboard_id", "046d:c31c").lower()
INPUT_WHEN_CONNECTED = CONFIG.get("input_connected", "15")
INPUT_WHEN_DISCONNECTED = CONFIG.get("input_disconnected", "18")

context = pyudev.Context()


def is_keyboard_connected() -> bool:
    for device in context.list_devices(subsystem="usb"):
        vid = device.get("ID_VENDOR_ID", "")
        pid = device.get("ID_MODEL_ID", "")
        if f"{vid}:{pid}".lower() == KEYBOARD_IDENTIFIER:
            return True
    return False


def switch_input(input_code: str):
    try:
        subprocess.run([DDCUTIL_CMD, "--bus", MONITOR_BUS, "setvcp", "60", str(input_code)], check=True)
        log_event(f"Switched input to {input_code}")
    except Exception as e:
        log_event(f"Failed to switch input: {e}")


def toggle_input(icon_obj, item):
    global current_manual_state, icon
    current_manual_state = not current_manual_state
    if current_manual_state:
        switch_input(INPUT_WHEN_CONNECTED)
        icon.title = "USB Monitor (Connected)"
    else:
        switch_input(INPUT_WHEN_DISCONNECTED)
        icon.title = "USB Monitor (Disconnected)"


def main_loop():
    last_state = None
    time.sleep(10)
    while True:
        connected = is_keyboard_connected()
        if last_state is None:
            if connected:
                switch_input(INPUT_WHEN_CONNECTED)
            else:
                switch_input(INPUT_WHEN_DISCONNECTED)
            last_state = connected
        elif connected != last_state:
            if connected:
                switch_input(INPUT_WHEN_CONNECTED)
            else:
                switch_input(INPUT_WHEN_DISCONNECTED)
            last_state = connected
        time.sleep(2)


def create_tray_icon():
    global icon
    icon_path = os.path.join(os.path.dirname(__file__), "..", "monitornew.ico")
    try:
        image = Image.open(icon_path)
    except Exception:
        image = Image.new("RGB", (64, 64), color=(0, 0, 0))
    menu = Menu(
        MenuItem("Switch Monitor Port", toggle_input),
        Menu.SEPARATOR,
        MenuItem("Edit Settings", lambda icon, item: threading.Thread(target=show_settings_popup).start()),
        MenuItem("Show Logs", lambda icon, item: threading.Thread(target=open_log_file).start()),
        Menu.SEPARATOR,
        MenuItem("Stop Service", quit_app),
    )
    icon = Icon("USBMonitor", image, "USB Monitor", menu)
    threading.Thread(target=main_loop, daemon=True).start()
    icon.run()


def quit_app(icon, item):
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
