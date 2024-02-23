import pyudev

def find_microphone():
    mic_name = "USB_PnP_Sound_Device"
    mic_connected = False

    context = pyudev.Context()
    for device in context.list_devices():
        if mic_name in str(device.get('ID_MODEL')):
            mic_connected = True
    
    return mic_connected

"""
import os

dev_folders = os.listdir("/dev")
hid_files = [] # Human Interface Device

for folder in dev_folders:
    if "hidraw" in str(folder):
        hid_files.append(str(folder))


print(hid_files)
"""