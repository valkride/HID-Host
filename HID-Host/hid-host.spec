# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

# Add current directory to path to find hid-config.json
a = Analysis(
    ['hid-host.py'],
    pathex=['.'],
    binaries=[],
    datas=[('hid-config.json', '.')],
    hiddenimports=[
        'hid',
        'psutil',
        'GPUtil',
        'pycaw.pycaw',
        'comtypes',
        'win32pdh',
        'ctypes',
        'ctypes.wintypes'
    ],
    hookspath=['.'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Try to collect hidapi binaries
try:
    from PyInstaller.utils.hooks import collect_dynamic_libs
    hidapi_binaries = collect_dynamic_libs('hid')
    if hidapi_binaries:
        a.binaries += hidapi_binaries
        print(f"Found {len(hidapi_binaries)} hidapi binaries")
    else:
        print("No hidapi binaries found automatically")
except Exception as e:
    print(f"Could not auto-collect hidapi binaries: {e}")

# Manually add common hidapi DLL locations for Windows
potential_dlls = [
    'hidapi.dll',
    'libhidapi-0.dll',
    'hid.dll'
]

# Try to find hidapi DLLs in Python site-packages
try:
    import hid
    hid_dir = os.path.dirname(hid.__file__)
    print(f"HID module directory: {hid_dir}")
    
    for dll_name in potential_dlls:
        dll_path = os.path.join(hid_dir, dll_name)
        if os.path.exists(dll_path):
            print(f"Found DLL: {dll_path}")
            a.binaries += [(dll_name, dll_path, 'BINARY')]
        else:
            print(f"DLL not found: {dll_path}")
            
except Exception as e:
    print(f"Could not locate hid module: {e}")

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='hid-host',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX to avoid issues
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
