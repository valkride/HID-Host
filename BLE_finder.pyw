import sys
import hid
import asyncio
import threading
import requests
from bleak import BleakScanner
from PyQt5 import QtWidgets, QtCore, QtGui

mac_vendor_cache = {}
def get_mac_vendor(mac):
    prefix = mac.upper().replace(":", "")[0:6]
    if prefix in mac_vendor_cache:
        return mac_vendor_cache[prefix]
    try:
        resp = requests.get(f"https://api.macvendors.com/{mac}", timeout=2)
        if resp.status_code == 200:
            vendor = resp.text.strip()
            mac_vendor_cache[prefix] = vendor
            return vendor
    except Exception:
        pass
    return "Unknown"

class DeviceTable(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(12)
        self.setHorizontalHeaderLabels([
            "Type", "VID", "PID", "Name", "Manufacturer", "Product", "Serial", "Path/Address", "MAC Vendor", "RSSI", "BLE Manufacturer Data", "Active"
        ])
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu)
        self.cellDoubleClicked.connect(self.copy_cell)
        self.setStyleSheet("QTableWidget::item:selected { background: #cce6ff; }")

    def context_menu(self, pos):
        menu = QtWidgets.QMenu()
        copy_action = menu.addAction("Copy Cell")
        action = menu.exec_(self.viewport().mapToGlobal(pos))
        if action == copy_action:
            self.copy_cell()

    def copy_cell(self, row=None, col=None):
        if row is None or col is None:
            items = self.selectedItems()
            if not items:
                return
            item = items[0]
            value = item.text()
        else:
            value = self.item(row, col).text()
        QtWidgets.QApplication.clipboard().setText(value)

class VIDPIDFinderApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HID & BLE Device Table")
        self.resize(1100, 500)
        layout = QtWidgets.QVBoxLayout(self)
        self.table = DeviceTable(self)
        layout.addWidget(self.table)
        btn_layout = QtWidgets.QHBoxLayout()
        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.populate_devices)
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        self.status = QtWidgets.QLabel("")
        layout.addWidget(self.status)
        self.populate_devices()

    def populate_devices(self):
        self.table.setRowCount(0)
        CORRECT_PATH = b'\\?\HID#{00001812-0000-1000-8000-00805f9b34fb}_Dev_VID&011d50_PID&615e_REV&0001_dc1558ce8544#c&1565a40e&0&0000#{4d1e55b2-f16f-11cf-88cb-001111000030}'
        # HID devices
        try:
            devices = hid.enumerate()
            for d in devices:
                vid = f"0x{d['vendor_id']:04X}"
                pid = f"0x{d['product_id']:04X}"
                name = d.get('product_string', '') or ''
                manufacturer = d.get('manufacturer_string', '') or ''
                product = d.get('product_string', '') or ''
                serial = d.get('serial_number', '') or ''
                path = d.get('path', '') or ''
                mac_vendor = ""
                if isinstance(path, str) and ":" in path:
                    mac = path.split(":")[-6:]
                    if len(mac) == 6:
                        mac_addr = ":".join(mac)
                        mac_vendor = get_mac_vendor(mac_addr)
                # Mark as active if path matches CORRECT_PATH (bytes or str)
                is_active = "✔" if path == CORRECT_PATH or (isinstance(path, bytes) and path == CORRECT_PATH) or (isinstance(path, str) and path == CORRECT_PATH.decode(errors='ignore')) else ""
                row = self.table.rowCount()
                self.table.insertRow(row)
                for col, val in enumerate(["HID", vid, pid, name, manufacturer, product, serial, path, mac_vendor, "", "", is_active]):
                    item = QtWidgets.QTableWidgetItem(str(val))
                    self.table.setItem(row, col, item)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to enumerate HID devices:\n{e}")
            self.status.setText("Failed to enumerate HID devices.")
        # BLE devices (broadcast)
        def scan_ble():
            try:
                devices = asyncio.run(BleakScanner.discover(timeout=5.0, return_adv=True))
                for device, adv in devices.values():
                    name = device.name or adv.local_name or "Unknown"
                    address = device.address
                    rssi = device.rssi
                    manufacturer = ""
                    product = ""
                    serial = ""
                    path = address
                    mac_vendor = ""
                    if ":" in address:
                        mac = address.split(":")[-6:]
                        if len(mac) == 6:
                            mac_addr = ":".join(mac)
                            mac_vendor = get_mac_vendor(mac_addr)
                    ble_manuf = (
                        ", ".join(f"{k}: {v.hex()}" for k, v in adv.manufacturer_data.items()) if adv.manufacturer_data else ""
                    )
                    row = self.table.rowCount()
                    self.table.insertRow(row)
                    for col, val in enumerate(["BLE", "", "", name, manufacturer, product, serial, path, mac_vendor, rssi, ble_manuf, ""]):
                        item = QtWidgets.QTableWidgetItem(str(val))
                        self.table.setItem(row, col, item)
                self.status.setText("HID and BLE scan complete.")
            except Exception as e:
                self.status.setText(f"BLE scan error: {e}")
        threading.Thread(target=scan_ble, daemon=True).start()

def main():
    app = QtWidgets.QApplication(sys.argv)
    win = VIDPIDFinderApp()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()