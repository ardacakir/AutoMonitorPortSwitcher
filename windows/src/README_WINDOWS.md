# Auto Monitor Port Switcher (Windows Version - Archived)

This is the **archived Windows version** of the Auto Monitor Port Switcher project.  
It is no longer actively maintained but provided here for reference and historical builds.

---

## ⚠️ Status

- ✅ Last known working version: **Windows 11 24H2**
- ❌ No future support or bug fixes
- ✅ Linux version is now the only supported and maintained version

---

## 📁 Folder Structure

- `windows/Releases/` — Frozen `.exe` builds created with `pyinstaller`
- `windows/src/` — Python source code used for building the `.exe`

---

## 🧪 Features (Windows)

- Detect USB device (keyboard) and switch monitor input using **DDC/CI**
- Tray icon for background operation
- Settings stored in JSON config file
- Compatible with Windows 10/11

---

## ⚙️ Build Instructions (Optional)

> Requires Python 3.10 or 3.11 and `pyinstaller`

```bash
cd windows/src/
pip install -r requirements.txt
pyinstaller --clean --noconsole --onefile --icon=usb_monitor.ico --name=usb_monitor usb_monitor.py
```

Result will be under `dist/usb_monitor.exe`.

---

## ❌ Known Issues (Windows)

- Windows updates sometimes break DDC/CI access
- Tray icon not visible if `.ico` has wrong dimensions
- Behavior under UAC or multiple monitors may be inconsistent

---

## 🪪 License

MIT License – see [../LICENSE](../LICENSE)

---

## 🔁 Switch to Linux

We recommend switching to the actively maintained [Linux version](../linux/README_LINUX.md) if you're using Fedora KDE or any modern Linux distribution.

