# PyInstaller hook for hidapi
from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files

# Collect all hidapi dynamic libraries
binaries = collect_dynamic_libs('hid')

# Also try to collect any data files
datas = collect_data_files('hid')

# Add hidden imports that might be needed
hiddenimports = ['hid', 'ctypes', 'ctypes.wintypes']
