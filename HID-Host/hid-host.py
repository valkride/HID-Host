# System Resource Monitor
# Shows CPU, RAM, GPU, and Disk usage

import psutil
import time
try:
    import GPUtil
    gpu_available = True
except ImportError:
    gpu_available = False
import hid
import json
import os

# Load HID device config from JSON, create default if missing
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'hid-config.json')
def load_hid_config():
    default_cfg = {
        "vendor_id": "",
        "product_id": "",
        "report_size": 32,
        "interval": 10,
        "recheck_interval": 10,
        "send_cpu": "y",
        "send_ram": "y",
        "send_gpu": "y",
        "send_disk": "y",
        "send_date": "y",
        "send_time": "y",
        "send_volume": "y"
    }
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'w') as f:
            json.dump(default_cfg, f, indent=2)
        raise RuntimeError(f"Created default {CONFIG_PATH}. Please fill in your device info and restart.")
    try:
        with open(CONFIG_PATH, 'r') as f:
            cfg = json.load(f)
            if not (cfg.get('vendor_id') and cfg.get('product_id')):
                raise RuntimeError(f"Please fill in all required fields in {CONFIG_PATH} and restart.")
            return (
                cfg.get('vendor_id'),
                cfg.get('product_id'),
                cfg.get('report_size', 32),
                cfg.get('interval', 10),
                cfg.get('recheck_interval', 10),                cfg.get('send_cpu', 'y'),
                cfg.get('send_ram', 'y'),
                cfg.get('send_gpu', 'y'),
                cfg.get('send_disk', 'y'),
                cfg.get('send_date', 'y'),
                cfg.get('send_time', 'y'),
                cfg.get('send_volume', 'y')
            )
    except Exception as e:
        raise RuntimeError(f"Failed to load {CONFIG_PATH}: {e}")

vendor_id, product_id, report_size, send_interval, recheck_interval, send_cpu, send_ram, send_gpu, send_disk, send_date, send_time, send_volume = load_hid_config()
VENDOR_ID = int(vendor_id, 0) if isinstance(vendor_id, str) else int(vendor_id)
PRODUCT_ID = int(product_id, 0) if isinstance(product_id, str) else int(product_id)
REPORT_SIZE = int(report_size)
SEND_INTERVAL = int(send_interval)
RECHECK_INTERVAL = int(recheck_interval)
SEND_CPU = send_cpu.lower() == 'y'
SEND_RAM = send_ram.lower() == 'y'
SEND_GPU = send_gpu.lower() == 'y'
SEND_DISK = send_disk.lower() == 'y'
SEND_DATE = send_date.lower() == 'y'
SEND_TIME = send_time.lower() == 'y'
SEND_VOLUME = send_volume.lower() == 'y'

def show_cpu():
    print(f"CPU: {psutil.cpu_percent(interval=1)}%")

def show_ram():
    mem = psutil.virtual_memory()
    print(f"RAM: {mem.percent}%")

def show_disk():
    # Show usage for the system drive only (like Task Manager default)
    usage = psutil.disk_usage(psutil.disk_partitions()[0].mountpoint)
    print(f"Disk: {usage.percent}%")

def get_gpu_usage():
    import platform, time
    system = platform.system()
    # Try GPUtil (NVIDIA/AMD/Intel, cross-platform)
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        if gpus:
            return int(max([gpu.load * 100 for gpu in gpus]))
    except Exception:
        pass
    # Try Windows Performance Counters (Windows only)
    if system == "Windows":
        try:
            import win32pdh
            items, instances = win32pdh.EnumObjectItems(None, None, 'GPU Engine', win32pdh.PERF_DETAIL_WIZARD)
            usage_values = []
            for instance in instances:
                if 'engtype_3D' in instance:
                    hq = win32pdh.OpenQuery()
                    counter_path = f'\\GPU Engine({instance})\\Utilization Percentage'
                    hci = win32pdh.AddCounter(hq, counter_path)
                    win32pdh.CollectQueryData(hq)
                    time.sleep(0.1)
                    win32pdh.CollectQueryData(hq)
                    _, val = win32pdh.GetFormattedCounterValue(hci, win32pdh.PDH_FMT_LONG)
                    usage_values.append(val)
                    win32pdh.CloseQuery(hq)
            if usage_values:
                return int(max(usage_values))
        except Exception:
            pass
    # If not Windows or nothing found, fallback to 0
    return 0

def show_gpu():
    usage = get_gpu_usage()
    print(f"GPU: {usage}%")

def find_raw_hid_path(vendor_id, product_id):
    for d in hid.enumerate():
        if d['vendor_id'] == vendor_id and d['product_id'] == product_id:
            return d['path']
    return None

def list_writeable_hid_paths(vendor_id, product_id, report):
    print("Checking all HID paths for VID=0x%04X PID=0x%04X..." % (vendor_id, product_id))
    found = False
    writeable_paths = []
    for d in hid.enumerate():
        if d['vendor_id'] == vendor_id and d['product_id'] == product_id:
            path = d['path']
            # Skip keyboard/mouse interfaces
            if b'KBD' in path or b'MOUSE' in path:
                print(f"Skipping {path} (keyboard/mouse interface)")
                continue
            print(f"Testing path: {path}")
            try:
                h = hid.device()
                h.open_path(path)
                result = h.write(report)
                h.close()
                if result > 0:
                    print(f"  -> Writeable (write returned {result})")
                    writeable_paths.append(path)
                else:
                    print("  -> Not writeable (write returned 0)")
            except Exception as e:
                print(f"  -> Not writeable (exception: {e})")
            found = True
    if not found:
        print("No HID devices found for this VID/PID.")
    return writeable_paths

writeable_path_cache = {'path': None, 'counter': 0}
# RECHECK_INTERVAL is now loaded from config

def get_volume_percent():
    try:
        import ctypes
        from ctypes import POINTER, cast
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        # GetMasterVolumeLevelScalar returns 0.0 to 1.0
        return int(round(volume.GetMasterVolumeLevelScalar() * 100))
    except Exception:
        return 0

def send_stats_via_ble(cpu, ram, disk, gpu):
    global writeable_path_cache
    import datetime
    # Always send stats in fixed byte positions:
    stat_fields = [
        f"{int(cpu):03d}" if SEND_CPU else "000",   # CPU: bytes 0-2
        f"{int(ram):03d}" if SEND_RAM else "000",   # RAM: bytes 3-5
        f"{int(gpu):03d}" if SEND_GPU else "000",   # GPU: bytes 6-8
        f"{int(disk):03d}" if SEND_DISK else "000"  # Disk: bytes 9-11
    ]
    # Date: DDMMYY (6 bytes, bytes 12-17)
    if SEND_DATE:
        now = datetime.datetime.now()
        date_str = now.strftime("%d%m%y")
    else:
        date_str = "000000"
    # Time: HHMM (4 bytes, bytes 18-21)
    if SEND_TIME:
        now = datetime.datetime.now()
        time_str = now.strftime("%H%M")
    else:
        time_str = "0000"
    # Volume: 3 bytes, bytes 22-24
    if SEND_VOLUME:
        vol = get_volume_percent()
        vol_str = f"{int(vol):03d}"
    else:
        vol_str = "000"    # Build the full report
    stats_bytes = ''.join(stat_fields).encode("ascii")  # 12 bytes
    date_bytes = date_str.encode("ascii")               # 6 bytes
    time_bytes = time_str.encode("ascii")               # 4 bytes
    vol_bytes = vol_str.encode("ascii")                 # 3 bytes
    report = bytearray(REPORT_SIZE)
    report[0] = 0                                       # Start with 0 byte
    report[1:1+len(stats_bytes)] = stats_bytes          # 1-12
    report[13:19] = date_bytes                          # 13-18
    report[19:23] = time_bytes                          # 19-22
    report[23:26] = vol_bytes                           # 23-25
    # Only re-check all paths every RECHECK_INTERVAL cycles
    writeable_path_cache['counter'] += 1
    if writeable_path_cache['path'] is None or writeable_path_cache['counter'] >= RECHECK_INTERVAL:
        writeable_paths = list_writeable_hid_paths(VENDOR_ID, PRODUCT_ID, report)
        if not writeable_paths:
            print("No writeable HID device found (by VID/PID). Is it connected?")
            writeable_path_cache['path'] = None
            writeable_path_cache['counter'] = 0
            return
        writeable_path_cache['path'] = writeable_paths[0]
        writeable_path_cache['counter'] = 0
    path = writeable_path_cache['path']
    try:
        h = hid.device()
        h.open_path(path)
        print(f"Device opened successfully: {path}")
        result = h.write(report)
        if result > 0:
            print("Report sent to device (OS accepted write).")
        else:
            print("Write returned 0 (no bytes written).")
        h.close()
        print(f"Sent HID report: {report}")
    except Exception as e:
        print(f"Failed to open/write to device: {e}")

def send_test_pattern():
    """Send a simple test pattern: 0, 1, 2, 3, 4, ... up to report size."""
    global writeable_path_cache
    # Create incrementing byte array starting with 0: 0, 1, 2, 3, ...
    report = bytearray(i % 256 for i in range(REPORT_SIZE))
    print(f"Sending test pattern: {list(report)}")
    # Find writeable path if needed
    writeable_path_cache['counter'] += 1
    if writeable_path_cache['path'] is None or writeable_path_cache['counter'] >= RECHECK_INTERVAL:
        writeable_paths = list_writeable_hid_paths(VENDOR_ID, PRODUCT_ID, report)
        if not writeable_paths:
            print("No writeable HID device found (by VID/PID). Is it connected?")
            writeable_path_cache['path'] = None
            writeable_path_cache['counter'] = 0
            return
        writeable_path_cache['path'] = writeable_paths[0]
        writeable_path_cache['counter'] = 0
    path = writeable_path_cache['path']
    try:
        h = hid.device()
        h.open_path(path)
        print(f"Device opened successfully: {path}")
        result = h.write(report)
        if result > 0:
            print("Test pattern sent to device (OS accepted write).")
        else:
            print("Write returned 0 (no bytes written).")
        h.close()
        print(f"Sent test pattern: {list(report)}")
    except Exception as e:
        print(f"Failed to open/write to device: {e}")

def test_mode():
    """Run in test mode - send incrementing byte pattern repeatedly"""
    print("Running in TEST MODE - sending 1,2,3... byte pattern")
    while True:
        send_test_pattern()
        time.sleep(SEND_INTERVAL)

def main():
    while True:
        cpu = int(psutil.cpu_percent(interval=1))
        ram = int(psutil.virtual_memory().percent)
        disk = int(psutil.disk_usage(psutil.disk_partitions()[0].mountpoint).percent)
        gpu = int(get_gpu_usage())
        send_stats_via_ble(cpu, ram, disk, gpu)
        # Removed per user request: no need to print stats to console
        # print(f"CPU: {cpu}%")
        # print(f"RAM: {ram}%")
        # print(f"GPU: {gpu}%")
        # print(f"Disk: {disk}%")
        # Wait for the full interval (including the 1s cpu_percent sample)
        time.sleep(max(SEND_INTERVAL, 1))

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1].lower() == "test":
        test_mode()
    else:
        main()
