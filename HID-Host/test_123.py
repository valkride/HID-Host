#!/usr/bin/env python3
"""
Simple HID test script that sends 1,2,3... byte pattern
"""
import hid
import time
import json
import os

# Load config
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'hid-config.json')
with open(CONFIG_PATH, 'r') as f:
    cfg = json.load(f)

VENDOR_ID = int(cfg['vendor_id'], 0) if isinstance(cfg['vendor_id'], str) else int(cfg['vendor_id'])
PRODUCT_ID = int(cfg['product_id'], 0) if isinstance(cfg['product_id'], str) else int(cfg['product_id'])
REPORT_SIZE = int(cfg['report_size'])

print(f"Looking for HID device VID=0x{VENDOR_ID:04X} PID=0x{PRODUCT_ID:04X}")

def find_hid_device():
    """Find and return all HID device paths, test which ones are writeable"""
    devices = []
    for d in hid.enumerate():
        if d['vendor_id'] == VENDOR_ID and d['product_id'] == PRODUCT_ID:
            devices.append(d)
    
    print(f"Found {len(devices)} matching devices:")
    for i, d in enumerate(devices):
        path = d['path']
        usage_page = d.get('usage_page', 'unknown')
        usage = d.get('usage', 'unknown')
        interface = d.get('interface_number', 'unknown')
        print(f"  {i}: {path}")
        print(f"      Usage Page: {usage_page}, Usage: {usage}, Interface: {interface}")
    
    # Test each device to see which one accepts writes
    for i, d in enumerate(devices):
        path = d['path']
        # Skip keyboard/mouse interfaces (these usually don't accept raw writes)
        if b'KBD' in path or b'MOUSE' in path:
            print(f"  Skipping {i}: appears to be keyboard/mouse interface")
            continue
            
        print(f"  Testing device {i} for writeability...")
        test_report = bytearray([1, 2, 3, 4])  # Small test pattern
        try:
            h = hid.device()
            h.open_path(path)
            result = h.write(test_report)
            h.close()
            if result > 0:
                print(f"  ✓ Device {i} is writeable (wrote {result} bytes)")
                return path
            else:
                print(f"  ✗ Device {i} write failed (returned {result})")
        except Exception as e:
            print(f"  ✗ Device {i} error: {e}")
    
    print("No writeable device found!")
    return None

def send_123_pattern():
    """Send exactly 1,2,3,4... pattern"""
    # Create simple 1,2,3... pattern
    report = bytearray()
    for i in range(REPORT_SIZE):
        report.append((i + 1) % 256)
    
    print(f"Test pattern ({REPORT_SIZE} bytes): {list(report)}")
    
    path = find_hid_device()
    if not path:
        print("No HID device found!")
        return False
    
    try:
        h = hid.device()
        h.open_path(path)
        print(f"Device opened: {path}")
        
        result = h.write(report)
        print(f"Write result: {result} bytes")
        
        h.close()
        print("Device closed")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("=== HID 123 Pattern Test ===")
    while True:
        success = send_123_pattern()
        if not success:
            print("Failed to send pattern")
        print("-" * 40)
        time.sleep(2)
