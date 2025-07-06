#!/usr/bin/env python3
import os
import logging
from logging.handlers import RotatingFileHandler

# Configure environment for Wayland sessions when available
if os.environ.get("XDG_SESSION_TYPE") == "wayland" or os.environ.get("WAYLAND_DISPLAY"):
    os.environ.setdefault("PYSTRAY_BACKEND", "appindicator")
    os.environ.setdefault("GDK_BACKEND", "wayland")
    os.environ.setdefault("QT_QPA_PLATFORM", "wayland")

import sys
import time
import json
import subprocess
import threading

import pyudev
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

# Logger will be configured once at startup
logger = None

def setup_logging() -> None:
    """Initialize rotating file logging."""
    global logger
    log_dir = os.path.join(APP_DATA, "logs")
    os.makedirs(log_dir, exist_ok=True)
    logger = logging.getLogger("usb_monitor")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = RotatingFileHandler(
            LOG_FILE, maxBytes=1024 * 1024, backupCount=3, encoding="utf-8"
        )
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

def is_wayland() -> bool:
    """Return True if running under a Wayland session."""
    return os.environ.get("XDG_SESSION_TYPE") == "wayland" or bool(os.environ.get("WAYLAND_DISPLAY"))

def is_headless():
    return not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY")

def check_single_instance():
    if os.path.exists(LOCK_FILE):
        print("Another instance is already running. Exiting.")
        sys.exit(0)
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))


def remove_lock_file():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)


def log_event(message: str, level: int = logging.INFO) -> None:
    """Record a log message using the configured logger."""
    if logger is None:
        setup_logging()
    logger.log(level, message)


def open_log_file():
    """Open the log file using the user's preferred editor or default handler."""
    if not os.path.exists(LOG_FILE):
        if is_headless():
            print("Log file not found.")
        else:
            messagebox.showinfo("USB Monitor", "Log file not found.")
        return

    if is_headless():
        print(f"Log file located at: {LOG_FILE}")
        return

    try:
        env = os.environ.copy()
        if is_wayland():
            env.setdefault("QT_QPA_PLATFORM", "wayland")
        subprocess.Popen(["xdg-open", LOG_FILE], env=env)
    except Exception as e:
        log_event(f"xdg-open failed: {e}", level=logging.ERROR)
        if not is_headless():
            messagebox.showerror("USB Monitor", f"Could not open log file:\n{e}")


def ensure_settings_file():
    os.makedirs(APP_DATA, exist_ok=True)
    if not os.path.exists(SETTINGS_FILE):
        if is_headless():
            print("Headless environment detected. Creating default settings.json...")
            default_config = {
                "monitor_bus": "1",
                "keyboard_id": "046d:c31c",
                "input_connected": "15",
                "input_disconnected": "18"
            }
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=4)
        else:
            show_settings_popup()


def show_settings_popup():
    existing = {
        "monitor_bus": "1",
        "keyboard_id": "046d:c31c",
        "input_connected": "15",
        "input_disconnected": "18",
    }
    if is_headless():
        print("Headless environment detected. Skipping settings popup.")
        return
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

    try:
        root = tk.Tk()
    except tk.TclError as e:
        log_event(f"Failed to open settings popup: {e}")
        return
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
    from pystray import Icon, Menu, MenuItem
    global icon
    icon_path = os.path.join(os.path.dirname(__file__), "monitor.png")
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
    setup_logging()
    log_event("Script started")
    try:
        if is_headless():
            log_event("Headless mode detected. Running monitor logic only.")
            threading.Thread(target=main_loop, daemon=True).start()
            while True:
                time.sleep(60)  # Keep the script alive
        else:
            create_tray_icon()
    except KeyboardInterrupt:
        log_event("Script terminated by user.")
    except Exception as e:
        log_event(f"Script crashed: {e}")
    finally:
        remove_lock_file()
