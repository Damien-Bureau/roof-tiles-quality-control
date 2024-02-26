import os
import pyudev
import sounddevice as sd

def get_input_devices_list():
    devices = sd.query_devices()
    input_devices_names = []
    input_devices_id = []

#     print()
    for device in devices:
        if device.get('max_input_channels') > 0 and device.get('name') != 'pulse':
            device_id = device.get('index')
            device_name = device.get('name')
#             print(f"Input Device {device_id} - {device_name}")
            input_devices_names.append(device_name)
            input_devices_id.append(device_id)
    #print()
    
    return input_devices_names, input_devices_id


def set_default_audio_input_device(device_index):
    devices = sd.query_devices()
    old_default_device = devices[sd.default.device[0]].get('name')
    sd.default.device = device_index
    print(f"\nOld default device: {old_default_device}")
    print(f"New default device: {devices[sd.default.device[0]].get('name')}\n")



def find_microphone():
    mic_name = "USB_PnP_Sound_Device" # to change if a different microphone is used
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
