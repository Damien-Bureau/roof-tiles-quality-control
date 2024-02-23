import os
import pyudev

def find_microphone():
    mic_name = "USB_PnP_Sound_Device"
    mic_connected = False

    context = pyudev.Context()
    for device in context.list_devices():
        if mic_name in str(device.get('ID_MODEL')):
            mic_connected = True
    
    return mic_connected


def find_storage_device():
    devices_folders = os.listdir("/media/pi")
    if any(devices_folders):
        return devices_folders[0]
    else:
        return None
