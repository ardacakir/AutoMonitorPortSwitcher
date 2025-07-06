import wmi

c = wmi.WMI()
for usb in c.Win32_USBHub():
    print(usb.DeviceID, "|", usb.Name)
