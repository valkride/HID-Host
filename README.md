# HID-Host Project

This repository contains two main Python applications for working with HID and BLE devices on Windows:

- **BLE_finder.pyw**: A PyQt5 GUI tool to scan and display HID and BLE devices, including vendor info, RSSI, and more.
- **hid-host.pyw**: A system resource monitor that sends CPU, RAM, GPU, Disk, Date, Time, and Volume stats to a HID device, configurable via `hid-config.json`.

---

## Requirements

- Python 3.8+
- Windows OS (tested)
- Packages:
  - `hidapi` (install via `pip install hid`)
  - `bleak`
  - `PyQt5`
  - `psutil`
  - `GPUtil` (optional, for GPU stats)
  - `requests`
  - `pycaw` and `comtypes` (for volume stats, optional)

---

## BLE_finder.pyw

A GUI tool to scan and display HID and BLE devices.

**Features:**
- Lists HID and BLE devices with details (VID, PID, Name, Manufacturer, Serial, MAC Vendor, RSSI, etc.)
- Double-click or right-click to copy cell values
- Refresh button to rescan devices

**Usage:**
```sh
python BLE_finder.pyw
```

---

## hid-host.pyw

A system resource monitor that sends stats to a HID device.

**Setup:**
- On first run, `hid-config.json` is created. Fill in your device's `vendor_id` and `product_id`.
- Configure which stats to send in the JSON file.

**Usage:**
```sh
python HID-Host/hid-host.pyw
```

---

## Building Executables

You can use [PyInstaller](https://pyinstaller.org/) to create standalone `.exe` files for both scripts:

```sh
pip install pyinstaller
pyinstaller --onefile --windowed BLE_finder.pyw
pyinstaller --onefile --windowed HID-Host/hid-host.pyw
```

The executables will be in the `dist/` folder.

---

This is my take on a HID-HOST to send data to a wireless ZMK/QMK keyboard. feel free to apply it anywhere you see fit!
