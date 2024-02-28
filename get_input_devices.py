import sounddevice as sd

def get_input_devices_list():
    devices = sd.query_devices()
    input_devices_names = []
    input_devices_id = []

#     print()
    for device in devices:
        if device.get('max_input_channels') > 0 and device.get('max_output_channels') == 0 and '@System32' not in device['name'] and device.get('name') != 'pulse' :
            device_id = device.get('index')
            device_name = device.get('name')
#             print(f"Input Device {device_id} - {device_name}")
            input_devices_names.append(device_name)
            input_devices_id.append(device_id)
    #print()
    
    return input_devices_names, input_devices_id

def set_default_device(device_index):
    devices = sd.query_devices()
    old_default_device = devices[sd.default.device[0]].get('name')
    sd.default.device = device_index
    print(f"\nOld default device: {old_default_device}")
    print(f"New default device: {devices[sd.default.device[0]].get('name')}\n")
